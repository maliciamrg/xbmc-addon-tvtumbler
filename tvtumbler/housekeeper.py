'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import time
import xbmc


from . import logger, fastcache, blacklist
from .names import scene

_fastcache_expire_last_run = time.time()
_blacklist_expire_last_run = time.time()


def run():
    global _fastcache_expire_last_run, _blacklist_expire_last_run

    logger.debug('housekeeper - run')
    if xbmc.Player().isPlaying():
        logger.debug('XBMC is Playing, skipping housekeeping')
        return

    if time.time() - _fastcache_expire_last_run > 60 * 60 * 24:  # 24 hrs
        fastcache.expire_old_records()
        _fastcache_expire_last_run = time.time()

    if time.time() - _blacklist_expire_last_run > 60 * 60 * 36:  # 36 hrs
        blacklist.expire_old_records()
        _blacklist_expire_last_run = time.time()

    scene.update_if_needed()
