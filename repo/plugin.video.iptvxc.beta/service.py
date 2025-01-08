from resources.modules import control
from resources.caching import ini_cache, eqp_cache

if control.setting('first_run')=='false':
	eqp_cache.EPGUpdater().setup_database()
	eqp_cache.EPGUpdater().silent_update()
	ini_cache.silent_cache_update()