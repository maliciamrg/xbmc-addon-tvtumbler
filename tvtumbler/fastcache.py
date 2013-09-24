'''
This file is part of TvTumbler.

Created on Sep 19, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import cPickle
from functools import update_wrapper
import os
import time
import traceback
import xbmc
from . import logger, events


_cache = None


def func_cache(max_age_secs=60 * 60 * 24):
    def decorating_function(user_function):
        def wrapper(*args):
            global _cache
            if _cache is None:
                _load_fastcache()
            func_key = user_function.__module__ + '.' + user_function.__name__
            key = tuple(args)
            if func_key in _cache:
                if key in _cache[func_key] and (time.time() - _cache[func_key][key][0]) < max_age_secs:
                    return _cache[func_key][key][1]
            else:
                _cache[func_key] = {}

            result = user_function(*args)
            _cache[func_key][key] = (time.time(), result)
            return result

        def cache_clear():
            """Clear the cache"""
            func_key = user_function.__module__ + '.' + user_function.__name__
            if func_key in _cache:
                _cache[func_key] = {}

        def is_cached(*args):
            global _cache
            if _cache is None:
                _load_fastcache()
            func_key = user_function.__module__ + '.' + user_function.__name__
            if func_key in _cache:
                key = tuple(args)
                if key in _cache[func_key] and (time.time() - _cache[func_key][key][0]) < max_age_secs:
                    return True
            return False

        wrapper.__wrapped__ = user_function
        wrapper.cache_clear = cache_clear
        wrapper.is_cached = is_cached
        return update_wrapper(wrapper, user_function)

    return decorating_function


def _onAbortRequested():
    global _cache
    if _cache:
        pickle_file_path = _get_fastcache_pickle_path()
        logger.debug('Saving _cache to "%s"' % str(pickle_file_path))
        pickle_file = open(pickle_file_path, 'wb')
        cPickle.dump(_cache, pickle_file)
        pickle_file.close()

events.add_event_listener(events.ABORT_REQUESTED, _onAbortRequested)


def _get_fastcache_pickle_path():
    return os.path.join(xbmc.translatePath('special://temp').decode('utf-8'),
                                        'fc.pkl')


def _load_fastcache():
    global _cache
    if _cache is None:
        try:
            pickle_file_path = _get_fastcache_pickle_path()
            if os.path.exists(pickle_file_path):
                logger.debug('Loading _series_fastcache from "%s"' % str(pickle_file_path))
                pickle_file = open(pickle_file_path, 'rb')
                _cache = cPickle.load(pickle_file)
                pickle_file.close()
                return
        except Exception, e:
            logger.error('Error loading _series_fastcache from pickle: ' + str(e))
            logger.error(traceback.format_exc())
    _cache = {}


def expire_old_records(max_age_secs=60 * 60 * 48):
    global _cache
    logger.debug('Starting expire_old_records, with max_age_secs = ' + str(max_age_secs))
    num_deleted = 0
    now = time.time()
    if _cache is not None:
        for func_key in _cache.keys():
            for arg_key in _cache[func_key].keys():
                if now - _cache[func_key][arg_key][0] > max_age_secs:
                    del _cache[func_key][arg_key]
                    num_deleted = num_deleted + 1
    logger.debug('Deleted %d expired entries from the cache.' % (num_deleted,))
