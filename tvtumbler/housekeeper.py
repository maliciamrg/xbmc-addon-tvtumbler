'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import time
import xbmc


from . import logger, fastcache, blacklist, epdb
from .names import scene

_fastcache_expire_last_run = time.time()
_blacklist_expire_last_run = time.time()
_epdb_last_run = time.time()


def run():
    global _fastcache_expire_last_run, _blacklist_expire_last_run, _epdb_last_run

    logger.debug('housekeeper - run')
    if xbmc.Player().isPlaying():
        logger.debug('XBMC is Playing, skipping housekeeping')
        return

    from . import main

    if xbmc.abortRequested or main.shutdownRequested:
        return

    if time.time() - _fastcache_expire_last_run > 60 * 60 * 24:  # 24 hrs
        fastcache.expire_old_records()
        _fastcache_expire_last_run = time.time()

    if xbmc.abortRequested or main.shutdownRequested:
        return

    if time.time() - _blacklist_expire_last_run > 60 * 60 * 36:  # 36 hrs
        blacklist.expire_old_records()
        _blacklist_expire_last_run = time.time()

    if xbmc.abortRequested or main.shutdownRequested:
        return

    scene.update_if_needed()

    if xbmc.abortRequested or main.shutdownRequested:
        return

    # We try to refresh the shows every 42 minutes.  Only shows actually needing a refresh
    # will be refreshed.  We limit each run to 10 shows (the 10 oldest).
    if time.time() - _epdb_last_run > 60 * 42:
        epdb.refresh_needed_shows(show_limit=10)
        _epdb_last_run = time.time()

    logger.debug('housekeeper is finished')
