'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import sys
import xbmc
from . import logger
import time

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json


def exec_rpc(method, params=None):
    command = {
        'method': method,
        'id': 1,
        'jsonrpc': "2.0",
    }

    if params is not None:
        command['params'] = params

    cmd_json = json.dumps(command)
    logger.debug('JSONRPC << %s' % cmd_json)
    result_json = xbmc.executeJSONRPC(json.dumps(command))
    logger.debug('JSONRPC >> %s' % result_json)
    result = json.loads(result_json)
    return result['result']


def get_tv_shows(properties=["title", "year", "imdbnumber", "file"]
                 # , max_age_secs=300
                 ):
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#VideoLibrary.GetTVShows
    """
#     try:
#         lastResult = get_tv_shows._lastResult
#         lastProps = get_tv_shows._lastProps
#         lastRun = get_tv_shows._lastRun
#
#         if (time.time() - lastRun > max_age_secs or
#             set(lastProps) < set(properties)):
#             lastResult = None
#     except AttributeError:
#         lastResult = None
#
#    if not lastResult:
    if True:
        lastResult = exec_rpc(method="VideoLibrary.GetTVShows",
                              params={'properties': properties})
        get_tv_shows._lastRun = time.time()
        get_tv_shows._lastResult = lastResult
        get_tv_shows._lastProps = properties

    return lastResult['tvshows']


def get_tv_show_details(tvshowid,
                        properties=["title", "year", "imdbnumber", "file"]):
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#VideoLibrary.GetTVShowDetails
    """
    result = exec_rpc(method="VideoLibrary.GetTVShowDetails",
                      params={'tvshowid': tvshowid,
                              'properties': properties})
    return result['tvshowdetails']


def get_seasons(tvshowid,
                properties=['season']):
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#VideoLibrary.GetSeasons
    """
    return exec_rpc(method="VideoLibrary.GetSeasons",
                    params={'tvshowid': tvshowid,
                            'properties': properties})


def get_episodes(tvshowid, season=-1,
                 properties=['title', 'season', 'episode', 'file', 'tvshowid']):
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#VideoLibrary.GetEpisodes
    """
    result = exec_rpc(method="VideoLibrary.GetEpisodes",
                    params={'tvshowid': tvshowid,
                            'season': season,
                            'properties': properties})
    try:
        return result['episodes']
    except KeyError:
        # no 'episodes' => there are none in the season.
        return []


def get_episode_details(episodeid,
                        properties=['title', 'season', 'episode', 'file',
                                    'tvshowid']):
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#VideoLibrary.GetEpisodeDetails
    """
    result = exec_rpc(method="VideoLibrary.GetEpisodeDetails",
                    params={'episodeid': episodeid,
                            'properties': properties})
    return result['episodedetails']


def videolibrary_scan(directory=""):
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#VideoLibrary.Scan
    """
    return exec_rpc(method="VideoLibrary.Scan",
                    params={'directory': directory})


def application_get_properties(properties=['version', 'name']):  # also 'volume' and 'muted' available
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#Application.GetProperties
    """
    result = exec_rpc(method="Application.GetProperties",
                    params={'properties': properties})
    return result


