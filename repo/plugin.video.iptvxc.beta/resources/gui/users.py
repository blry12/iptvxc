import hashlib
from resources.modules import control,tools, variables


DB_USERS = os.path.join(ADDONDATA, "users.db")

class UserManager:
    def __init__(self):
        """Initialize the UserManager and ensure the database exists."""
        if not os.path.exists("ADDONDATA"):
            os.makedirs("ADDONDATA")
        self.setup_database()

    def setup_database(self):
        """Create the users table if it doesn't exist."""
        conn = sqlite3.connect(DB_USERS)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                service_name TEXT,
                dns TEXT,
                password TEXT,
                last_used DATETIME
            )
        ''')
        conn.commit()
        conn.close()

    def add_or_update_user(self, username, service_name, dns, password):
        """Add a new user or update an existing one."""
        conn = sqlite3.connect(DB_USERS)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, service_name, dns, password, last_used)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(username)
            DO UPDATE SET service_name=?, dns=?, password=?, last_used=?
        ''', (username, service_name, dns, password, datetime.now(),
              service_name, dns, password, datetime.now()))
        conn.commit()
        conn.close()

    def get_users(self):
        """Fetch all users from the database."""
        conn = sqlite3.connect(DB_USERS)
        cursor = conn.cursor()
        cursor.execute("SELECT username, service_name, dns FROM users ORDER BY last_used DESC")
        users = cursor.fetchall()
        conn.close()
        return users

    def delete_user(self, username):
        """Delete a user by username."""
        conn = sqlite3.connect(DB_USERS)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username=?", (username,))
        conn.commit()
        conn.close()

    def set_selected_account(self, username):
        """Set the selected account in persistent storage."""
        conn = sqlite3.connect(DB_USERS)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_used = ? WHERE username = ?", (datetime.now(), username))
        conn.commit()
        conn.close()

    def get_selected_account(self):
        """Get the most recently selected account."""
        conn = sqlite3.connect(DB_USERS)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, service_name, dns, password
            FROM users
            ORDER BY last_used DESC LIMIT 1
        """)
        selected_account = cursor.fetchone()
        conn.close()
        return selected_account

    def manage_users(self):
        """Menu to manage users."""
        users = self.get_users()
        user_options = [f"{user[2]} ({user[1]})" for user in users] + ["Add New User", "Delete User"]
        dialog = xbmcgui.Dialog()
        choice = dialog.select("Manage Users", user_options)

        if choice == -1:
            return None
        elif choice == len(user_options) - 2:  # Add New User
            service_name = dialog.input("Enter Service Name")
            username = dialog.input("Enter Username")
            dns = dialog.input("Enter DNS")
            password = dialog.input("Enter Password", option=xbmcgui.INPUT_ALPHANUM)
            if username and service_name and dns and password:
                self.add_or_update_user(username, service_name, dns, password)
                xbmcgui.Dialog().notification("User Added", f"{service_name} ({username}) added.", xbmcgui.NOTIFICATION_INFO, 3000)
        elif choice == len(user_options) - 1:  # Delete User
            username = dialog.input("Enter Username to Delete")
            if username:
                self.delete_user(username)
                xbmcgui.Dialog().notification("User Deleted", f"{username} removed.", xbmcgui.NOTIFICATION_INFO, 3000)
        else:  # Select User
            selected_user = users[choice]
            self.set_selected_account(selected_user[0])
            xbmcgui.Dialog().notification("Account Selected", f"Using DNS {selected_user[2]} for {selected_user[1]}.", xbmcgui.NOTIFICATION_INFO, 3000)
            return selected_user[2]

