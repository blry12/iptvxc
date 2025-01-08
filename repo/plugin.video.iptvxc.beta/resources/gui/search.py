import sqlite3
import os, base64
import re, xbmcgui, json
from resources.pyxbmct import addonwindow as pyxbmct
from resources.modules import control,tools, variables
DB_PATH = os.path.join(variables.ADDONDATA, "media_cache.db")
SEARCH_HISTORY_DB = "search_manager.db"


def entry():
	s = SearchManager()
	s.doModal()
	del s


class SearchManager(pyxbmct.AddonFullWindow):
	def __init__(self, title="Search Manager"):
		super().__init__(title)
		self.epg_data = []
		self.setGeometry(1280, 720, 20, 10)

		# Background
		background = pyxbmct.Image(variables.tvguidebg)
		self.placeControl(background, -3, -1, 25, 12)

		self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
		title_name = pyxbmct.Label(variables.ADDON_NAME, alignment=pyxbmct.ALIGN_CENTER)
		self.placeControl(title_name, -1, 4, 1, 5)

		# Search bar
		self.search_input = pyxbmct.Edit("Enter search term")
		self.placeControl(self.search_input, 0, 0, 1, 3)

		self.search_button = pyxbmct.Button("Search")
		self.placeControl(self.search_button, 0, 3, 1, 1)
		self.connect(self.search_button, self._perform_search)

		# Left list: Previously searched items
		self.category_list = pyxbmct.List(
			'font13', _itemTextXOffset=10, _itemTextYOffset=-3, _itemHeight=40, _space=10, _alignmentY=4
		)
		self.placeControl(self.category_list, 1, 0, 13, 3)
		self.connect(self.category_list, self._on_category_selected)

		# Right list: Search results
		self.results_list = pyxbmct.List(
			_itemTextXOffset=10, _itemTextYOffset=-3, _itemHeight=40, _space=10, _alignmentY=4
		)
		self.placeControl(self.results_list, 1, 3, 13, 7)
		#self.connect(self.results_list, self._on_result_highlighted)
		self.connectEventList(
			[pyxbmct.ACTION_MOVE_DOWN, pyxbmct.ACTION_MOVE_UP],
			self._on_result_highlighted
		)

		# Image and description
		self.channel_icon_label = pyxbmct.Image('')
		self.placeControl(self.channel_icon_label, 12, 0, 8, 2)

		self.channel_description_label = pyxbmct.TextBox()
		self.placeControl(self.channel_description_label, 12, 2, 8, 8)
		self.channel_description_label.setText('')
		self.channel_description_label.autoScroll(1000, 1000, 1000)

		# Navigation
		self.setFocus(self.search_input)
		#self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
		#self.connect(pyxbmct.ACTION_MOVE_DOWN, self._on_down_pressed)
		#self.connect(pyxbmct.ACTION_MOVE_UP, self._on_up_pressed)

		# Database initialization
		self.init_search_history_db()
		self._load_search_history()

	def init_search_history_db(self):
		"""Initialize the database for storing search history."""
		conn = sqlite3.connect(DB_PATH)
		cursor = conn.cursor()
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS search_history (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				search_term TEXT,
				last_searched DATETIME
			)
		''')
		conn.commit()
		conn.close()

	def _perform_search(self):
		"""Perform a search and display results."""
		search_term = self.search_input.getText().strip()
		if not search_term:
			return

		# Save to search history
		self._save_search_history(search_term)

		# Fetch results from the database
		results = self._search_database(search_term)

		# Populate results list
		self.results_list.reset()
		for result in results:
			label = f"{result['name']} ({result['table']})"
			self.results_list.addItem(label)

	def _save_search_history(self, search_term):
		"""Save the search term to the database."""
		conn = sqlite3.connect(DB_PATH)
		cursor = conn.cursor()
		cursor.execute('''
			INSERT INTO search_history (search_term, last_searched)
			VALUES (?, datetime('now'))
		''', (search_term,))
		conn.commit()
		conn.close()

		# Update previously searched items
		self._load_search_history()

	def _load_search_history(self):
		"""Load the search history into the left list."""
		conn = sqlite3.connect(DB_PATH)
		cursor = conn.cursor()
		cursor.execute('SELECT search_term FROM search_history ORDER BY last_searched DESC')
		search_terms = cursor.fetchall()
		conn.close()

		self.category_list.reset()
		for term in search_terms:
			self.category_list.addItem(term[0])

	def _search_database(self, search_term):
		"""Search all tables for the given term."""
		conn = sqlite3.connect(DB_PATH)
		cursor = conn.cursor()

		results = []

		# Search live_tv
		cursor.execute("SELECT stream_id, name FROM live_tv WHERE name LIKE ?", (f"%{search_term}%",))
		for row in cursor.fetchall():
			results.append({"id": row[0], "name": row[1], "table": "live_tv"})

		# Search vod
		cursor.execute("SELECT stream_id, name FROM vod WHERE name LIKE ?", (f"%{search_term}%",))
		for row in cursor.fetchall():
			results.append({"id": row[0], "name": row[1], "table": "vod"})

		# Search tv_series
		cursor.execute("SELECT series_id, name FROM tv_series WHERE name LIKE ?", (f"%{search_term}%",))
		for row in cursor.fetchall():
			results.append({"id": row[0], "name": row[1], "table": "tv_series"})

		conn.close()
		return results

	def _on_category_selected(self):
		"""Handle selection of a previously searched term."""
		selected_item = self.category_list.getSelectedItem()
		if selected_item:
			self.search_input.setText(selected_item.getLabel())

	def _on_result_highlighted(self):
		"""Handle highlighting of a search result."""
		selected_item = self.results_list.getSelectedItem()
		if selected_item:
			label = selected_item.getLabel()
			table = label.split('(')[-1].replace(')', '').strip()  # Get table type (live_tv, vod, tv_series)
			name = label.split('(')[0].strip()  # Get the name of the item

			conn = sqlite3.connect(DB_PATH)
			cursor = conn.cursor()

			if table == "live_tv":
				# Fetch live TV details (including stream_icon)
				cursor.execute("SELECT stream_icon, stream_id, epg_channel_id FROM live_tv WHERE name = ?", (name,))
				row = cursor.fetchone()
				
				if row:
					stream_icon, stream_id, epg_channel_id = row
					self.channel_icon_label.setImage(stream_icon)
					
					epg_data_from_db = load_epg_for_channel(epg_channel_id)
					now_program = "No data"
					now_description = "No Description Available"
					
					if epg_data_from_db:
						epg_data_from_db.sort(key=lambda x: x[2])
						current_time = int(time.time())
						for i, entry in enumerate(epg_data_from_db):
							start_time, end_time = entry[2], entry[3]
			
							if start_time <= current_time <= end_time:
								now_program = entry[1]
								now_description = entry[4]
								self.channel_description_label.setText(f"{name}\nNow: {now_program}\nNext: {now_description}")


			elif table == "vod":
				# Fetch VOD details (movie icon)
				import re
				cleaned_name = re.sub(r"\s*\(\d{4}\)$", "", name).strip()
				
				cursor.execute("SELECT stream_icon FROM vod WHERE TRIM(REPLACE(REPLACE(name, '(', ''), ')', '')) LIKE ?", (f"{cleaned_name}%",))
				row = cursor.fetchone()
				
				if row:
					stream_icon = row[0]
					self.channel_icon_label.setImage(stream_icon)
					# Fetch VOD movie details
					movie = {"name": name, "poster": stream_icon}
					self._update_movie_info(movie)
				else:
					tools.log(f"VOD entry not found for '{name}'")
					self.channel_description_label.setText(f"VOD Movie: {name} (Not Found in Database)")

			#figure out layout for seasons and episodes
			elif table == "tv_series":
				# Fetch TV Series details (cover image)
				cursor.execute("SELECT cover FROM tv_series WHERE name = ?", (name,))
				row = cursor.fetchone()
				if row:
					cover_image = row[0]
					self.channel_icon_label.setImage(cover_image)
					# Fetch series details dynamically
					series = {"name": name, "poster": cover_image}
					self._update_series_info(series)

			conn.close()



	def _format_program(self, program):
		"""Format a program's start and end time with its title."""
		try:
			start_time = datetime.fromtimestamp(int(program['start_timestamp'])).strftime('%H:%M')
			end_time = datetime.fromtimestamp(int(program['stop_timestamp'])).strftime('%H:%M')
			title = base64.b64decode(program['title']).decode('utf-8')
			return f"{start_time}-{end_time}: {title}"
		except (KeyError, ValueError, TypeError) as e:
			tools.log(f"Error formatting program: {e}")
			return "Invalid Program Data"



	def _update_movie_info(self, movie):
		tools.log(f"Fetching info for movie: {movie['name']}")

		tmdb_movie = self._get_movie_details(movie['name'])

		description = tmdb_movie.get('overview', 'No Description Available')
		plot = description 
		length = tmdb_movie.get('runtime', 'N/A')
		rating = tmdb_movie.get('vote_average', 'N/A')
		date = tmdb_movie.get('release_date', 'N/A')
		self.plot=plot

		movie_info = f"Plot: {plot}\n\nLength: {length} mins\nRating: {rating}/10\nRelease Date: {date}"

		self.channel_description_label.setText(movie_info)
		self.channel_icon_label.setImage(movie['poster'])

	def _get_movie_details(self, movie_name):
		api_key = '6ca3392e2903d0ddafc2dae3044ee31f'
		base_url = 'https://api.themoviedb.org/3'
		cleaned_movie_name = re.sub(r"[\s\-]\(?\d{4}\)?$", "", movie_name).strip()
		_movie_name = cleaned_movie_name.replace(' ', '+')
		search_url = f"{base_url}/search/movie?api_key={api_key}&query={_movie_name}&language=en-US"
		response = tools.OPEN_URL(search_url)
		search_results = json.loads(response)
		if search_results['results']:
			movie_id = search_results['results'][0]['id']
			details_url = f"{base_url}/movie/{movie_id}?api_key={api_key}&language=en-US"

			details_response = tools.OPEN_URL(details_url)
			search_results = json.loads(details_response)

			return json.loads(details_response)
		else:
			tools.log(f"No TMDb results found for movie: {movie_name}")
			return {}

	def _update_series_info(self, series):
		tools.log(f"Fetching info for series: {series['name']}")

		# Fetch series info (example: seasons, episodes)
		series_info = self._get_series_details(series['name'])

		description = series_info.get('overview', 'No Description Available')
		number_of_seasons = series_info.get('number_of_seasons', 'N/A')  # Fetch the number of seasons
		rating = series_info.get('vote_average', 'N/A')
		date = series_info.get('first_air_date', 'N/A')
		self.plot = description

		# Format the display text
		series_info_display = (
			f"Overview: {description}\n"
			f"Seasons: {number_of_seasons}\n"
			f"Rating: {rating}/10\n"
			f"First Air Date: {date}"
		)

		# Update UI elements
		self.channel_description_label.setText(series_info_display)
		self.channel_icon_label.setImage(series['poster'])


	def _get_series_details(self, series_name):
		api_key = '6ca3392e2903d0ddafc2dae3044ee31f'
		base_url = 'https://api.themoviedb.org/3'
		cleaned_series_name = re.sub(r"[\s\-]\(?\d{4}\)?$", "", series_name).strip()
		_series_name = cleaned_series_name.replace(' ', '+')
		search_url = f"{base_url}/search/tv?api_key={api_key}&query={_series_name}&language=en-US"
		response = tools.OPEN_URL(search_url)
		search_results = json.loads(response)

		if search_results['results']:
			series_id = search_results['results'][0]['id']
			details_url = f"{base_url}/tv/{series_id}?api_key={api_key}&language=en-US"
			details_response = tools.OPEN_URL(details_url)
			series_details = json.loads(details_response)

			return series_details
		else:
			tools.log(f"No TMDb results found for series: {series_name}")
			return {}

	def _play_stream(self, url, name, thumb, plot):
		liz = xbmcgui.ListItem(name)
		liz.setPath(url)
		liz.setArt({"thumb": thumb})
		liz.setProperty('IsPlayable', 'true')
		liz.setInfo('video', {'Plot': plot})
		liz.setMimeType('application/x-mpegURL')
		liz.setProperty('inputstream', 'inputstream.ffmpegdirect')
		liz.setProperty('inputstream.ffmpegdirect.manifest_type', 'hls')
		liz.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
		liz.setProperty('inputstream.ffmpegdirect.stream_mode', "timeshift")
		xbmc.Player().play(url, liz)


	def _on_down_pressed(self):
		"""Handle navigation down."""
		focused_control = self.getFocus()
		if focused_control == self.search_input:
			self.setFocus(self.category_list)
		elif focused_control == self.category_list:
			self.setFocus(self.results_list)


	def _go_back_to_stream(self):
		"""Handle going back to the stream."""
		self.close()

from datetime import datetime,timedelta
import time
def load_epg_for_channel(channel_id, offset=0):
	conn = sqlite3.connect(os.path.join(variables.ADDONDATA, "epg_cache.db"))
	cursor = conn.cursor()
	current_time = datetime.now() + timedelta(hours=offset)
	current_time = current_time.replace(microsecond=0)
	timestamp = int(current_time.timestamp())
	cursor.execute("SELECT * FROM epg WHERE channel_id=? AND start_time<=? AND end_time>=?", 
				   (channel_id, timestamp, timestamp))
	epg_data = cursor.fetchall()
	conn.close()
	return epg_data