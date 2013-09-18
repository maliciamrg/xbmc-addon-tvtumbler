'''
This file is part of TvTumbler.

This is a simple caching wrapper around tvdb_api.
(which supposedly has a cache also, but it extremely slow nonetheless)

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import cPickle
import os
import sys
import time
import traceback

import elementtree.ElementTree as etree
import requests
from tvdb_api import tvdb_api
import xbmc

from . import logger, events


TVDB_API_KEY = 'FCC2D40061D489B4'
_Tvdb = None  # This is a shared instance of tvdb_api.Tvdb.  Created when first needed
_tvdb_infos = {}
_series_fastcache = None  # this is a memory cache of /api/%s/series/%s/en.xml
SERIES_FASTCACHE_MAXAGE = 60 * 60 * 24


def _onAbortRequested():
    global _series_fastcache
    if _series_fastcache:
        pickle_file_path = _get_series_fastcache_pickle_path()
        logger.debug('Saving _series_fastcache to "%s"' % str(pickle_file_path))
        pickle_file = open(pickle_file_path, 'wb')
        cPickle.dump(_series_fastcache, pickle_file)
        pickle_file.close()

events.add_event_listener(events.ABORT_REQUESTED, _onAbortRequested)


def _get_series_fastcache_pickle_path():
    return os.path.join(xbmc.translatePath('special://temp').decode('utf-8'),
                                        'srsfc.pkl')


def _load_series_fastcache():
    global _series_fastcache
    if _series_fastcache is None:
        try:
            pickle_file_path = _get_series_fastcache_pickle_path()
            if os.path.exists(pickle_file_path):
                logger.debug('Loading _series_fastcache from "%s"' % str(pickle_file_path))
                pickle_file = open(pickle_file_path, 'rb')
                _series_fastcache = cPickle.load(pickle_file)
                pickle_file.close()
                return
        except Exception, e:
            logger.error('Error loading _series_fastcache from pickle: ' + str(e))
            logger.error(traceback.format_exc())
    _series_fastcache = {}


def get_tvdb_api_info(tvdb_id, maxage=60 * 60 * 24):
    global _Tvdb, _tvdb_infos
    if tvdb_id in _tvdb_infos:
        if time.time() - _tvdb_infos[tvdb_id][0] < maxage:
            return _tvdb_infos[tvdb_id][1]
    if _Tvdb is None:
        _Tvdb = tvdb_api.Tvdb(apikey=TVDB_API_KEY, debug=False)
    t = _Tvdb[int(tvdb_id)]
    _tvdb_infos[tvdb_id] = (time.time(), t)
    return t


def get_tvdb_field(tvdb_id, key_name, allow_remote_fetch=True):
    '''
    Get a (show-)field from the thetvdb by name.
    These will be the tags under 'Series' in something like
    http://thetvdb.com/api/813277AE7CCE5E14/series/248812/en.xml

    Note that the tags are forced to lowercase here.

    @return: the value in a top-level tags under 'Series' from thetvdb.  If the tag is a list (e.g. actors, genre),
        returns it as a list of strings.
        If there's no matching show, lookup fails, or the tag doesn't exists - returns None.
    @rtype: str|list|None
    '''
    result = tvdb_series_lookup(tvdb_id, allow_remote_fetch)
    if result and key_name.lower() in result:
        return result[key_name.lower()]
    else:
        return None

    # tvdb_api is just too slow for this kind of thing, it downloads and parses
    # episodes and all kinds of rubbish, just to get the name of the show.
    # so not using it here for now.
#     _tvdb_info = get_tvdb_api_info(tvdb_id)
#     if key_name in _tvdb_info.data:
#         return _tvdb_info[key_name]
#     return None


def get_episode_name(tvdb_id, season, episode):
    t = get_tvdb_api_info(tvdb_id)
    return t[season][episode]['episodename']


# This is used again.  tvdb_api is just too slow
def tvdb_series_lookup(tvdb_id, allow_remote_fetch=True):
    '''
    Look up a series from thetvdb.
    '''
    global _series_fastcache
    if _series_fastcache is None:
        _load_series_fastcache()
    if tvdb_id in _series_fastcache:
        if time.time() - _series_fastcache[tvdb_id][0] < SERIES_FASTCACHE_MAXAGE:
            return _series_fastcache[tvdb_id][1]
    if not allow_remote_fetch:
        return None
    l = _real_tvdb_series_lookup(tvdb_id)
    _series_fastcache[tvdb_id] = (time.time(), l)
    return l


def _real_tvdb_series_lookup(tvdb_id):
    url = 'http://thetvdb.com/api/%s/series/%s/en.xml' % (TVDB_API_KEY,
                                                          str(tvdb_id))
    logger.debug('getting url %s' % url)
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        # logger.debug('encoding is ' + r.encoding)
        logger.debug('raw data returned is ' + repr(r.text))
        data = r.text.encode('ascii', 'ignore')
    else:
        logger.notice('No data returned from tvdb for %s, ' +
                      'status code %d' % (tvdb_id, r.status_code))
        return None

    logger.debug(u'got data: %s' % data)
    parsedXML = etree.fromstring(data)
    series = parsedXML.find('Series')
    if not series:
        logger.debug('No series tag for %s' % tvdb_id)
        return None

    result = {}

    for c in series.findall('*'):
        if c.text:
            if c.text.startswith('|'):
                val = c.text.split('|')
            elif c.tag in ['banner', 'fanart', 'poster']:
                val = 'http://thetvdb.com/banners/' + c.text
            else:
                val = c.text
        else:
            val = None

        result[c.tag.lower()] = val

    return result

