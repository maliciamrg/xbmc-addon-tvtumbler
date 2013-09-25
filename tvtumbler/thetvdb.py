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

import xml.etree.ElementTree as etree
import requests  # @UnresolvedImport
from tvdb_api import tvdb_api
import xbmc

from . import logger, events, fastcache, db


TVDB_API_KEY = 'FCC2D40061D489B4'
_Tvdb = None  # This is a shared instance of tvdb_api.Tvdb.  Created when first needed
_tvdb_infos = {}


@fastcache.func_cache(max_age_secs=60 * 60 * 24)
def get_tvdb_api_info(tvdb_id):
    global _Tvdb
    if _Tvdb is None:
        _Tvdb = tvdb_api.Tvdb(apikey=TVDB_API_KEY, debug=False)
    return _Tvdb[int(tvdb_id)]


def get_tvdb_field(tvdb_id, key_name, allow_remote_fetch=True):
    '''
    Get a (show-)field from the thetvdb by name.
    These will be the tags under 'Series' in something like
    http://thetvdb.com/api/813277AE7CCE5E14/series/248812/en.xml

    Note that the tags are forced to lowercase here.

    @return: the value in a top-level tags under 'Series' from thetvdb.  If the tag is a list (e.g. actors, genre),
        returns it as a list of strings.
        If there's no matching show, lookup fails, or the tag doesn't exist - returns None.
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
    # there's a circular reference here: get_episode_name in epdb can call
    # get_tvdb_api_info from here, which is just silly.
    # @todo: refactor
    from . import epdb
    return epdb.get_episode_name(tvdb_id, season, episode)


# This is used again.  tvdb_api is just too slow
def tvdb_series_lookup(tvdb_id, allow_remote_fetch=True):
    '''
    Look up a series from thetvdb.
    '''
    if _real_tvdb_series_lookup.is_cached(tvdb_id) or allow_remote_fetch:
        return _real_tvdb_series_lookup(tvdb_id)
    return None


@fastcache.func_cache(max_age_secs=60 * 60 * 24)
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
