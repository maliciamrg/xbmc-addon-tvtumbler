'''
This file is part of TvTumbler.

This file contains all the calls to show-api.tvtumbler.com.

Created on Sep 7, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import time

from . import utils, logger


API_SERVER_BASE = 'http://show-api.tvtumbler.com/api/'
SHOW_CACHE_MAX_AGE_SECS = 60 * 60 * 24
_show_cache = {}


def show(tvdb_id):
    '''
    Look up a series.  Results are cached for SHOW_CACHE_MAX_AGE_SECS.

    @param tvdb_id: The tvdb_id
    @type tvdb_id: int
    @return: On failure, returns None, on Success returns a dict like the following:
                {"tv.com_id": "34391",
                "network": "BBC One",
                "showrss_id": "103",
                "zap2it_id": null,
                "tvdb_id": "78804",
                "series_name": "Doctor Who (2005)",
                "tvrage_id": "3332",
                "imdb_id": "tt0436992"}
    @rtype: dict
    '''
    global _show_cache, SHOW_CACHE_MAX_AGE_SECS
    if tvdb_id in _show_cache:
        last_val = _show_cache[tvdb_id]['val']
        last_run = _show_cache[tvdb_id]['age']
        if time.time() - last_run < SHOW_CACHE_MAX_AGE_SECS:
            return last_val

    url = API_SERVER_BASE + 'show?tvdb_id=' + str(tvdb_id)
    result = utils.get_url_as_json(url)
    if result and 'show' in result:
        _show_cache[tvdb_id] = {'val': result['show'], 'age': time.time()}
        return result['show']
    else:
        logger.notice(u'No "show" in result from %s, did get: %s' % (url, repr(result)))
        return None


def exceptions():
    '''
    /api/scene-names as a dict.

    @return: Returns the contents of /api/scene-names as a dict, or None on failure.
    @rtype: dict
    '''
    return utils.get_url_as_json(API_SERVER_BASE + 'scene-names')
