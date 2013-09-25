'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import sys
import xbmc
from . import logger, events
import time

if sys.version_info < (2, 7):
    import simplejson as json  # @UnresolvedImport
else:
    import json


def on_video_library_changed():
    logger.debug('Video library changed, resetting json cache related to it')
    clear_rpc_cache('VideoLibrary.GetTVShows')
    clear_rpc_cache('VideoLibrary.GetTVShowDetails')
    clear_rpc_cache('VideoLibrary.GetSeasons')
    clear_rpc_cache('VideoLibrary.GetEpisodes')

events.add_event_listener(events.VIDEO_LIBRARY_UPDATED, on_video_library_changed)

# This is a quick-and-dirty (but very fast) cache of rpc results.
# To clear the cache for a particular method, call clear_rpc_cache(method).
_rpc_cache = {}


class JsonRPCException(Exception):
    def __init__(self, message, code=None):
        self.message = message
        self.code = code


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
    if 'error' in result:
        raise JsonRPCException(result['error']['message'], result['error']['code'])

    return result['result']


def exec_rpc_with_cache(method, params=None, max_age_secs=7200):
    global _rpc_cache
    if not method in _rpc_cache:
        _rpc_cache[method] = {}
    repr_params = repr(params)
    if repr_params in _rpc_cache[method]:
        last_val = _rpc_cache[method][repr_params]['val']
        last_run = _rpc_cache[method][repr_params]['age']
        if time.time() - last_run < max_age_secs:
            return last_val  # still fresh!

    new_val = exec_rpc(method, params)
    _rpc_cache[method][repr_params] = {'val': new_val, 'age': time.time()}
    return new_val


def clear_rpc_cache(method):
    global _rpc_cache
    if method in _rpc_cache:
        del _rpc_cache[method]


def get_tv_shows(properties=["title", "year", "imdbnumber", "file"]
                 # , max_age_secs=300
                 ):
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#VideoLibrary.GetTVShows
    """
    result = exec_rpc_with_cache(method="VideoLibrary.GetTVShows",
                                 params={'properties': properties})
    return result['tvshows']


def get_tv_show_details(tvshowid,
                        properties=["title", "year", "imdbnumber", "file"]):
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#VideoLibrary.GetTVShowDetails
    """
    result = exec_rpc_with_cache(method="VideoLibrary.GetTVShowDetails",
                                 params={'tvshowid': tvshowid,
                                         'properties': properties})
    return result['tvshowdetails']


def get_seasons(tvshowid,
                properties=['season']):
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#VideoLibrary.GetSeasons
    """
    return exec_rpc_with_cache(method="VideoLibrary.GetSeasons",
                               params={'tvshowid': tvshowid,
                                       'properties': properties})


def get_episodes(tvshowid, season=-1,
                 properties=['title', 'season', 'episode', 'file', 'tvshowid']):
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#VideoLibrary.GetEpisodes
    """
    result = exec_rpc_with_cache(method="VideoLibrary.GetEpisodes",
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


def addons_execute_addon(addonid, params=[], wait=False):
    """
    http://wiki.xbmc.org/?title=JSON-RPC_API/v6#Addons.ExecuteAddon
    """
    result = exec_rpc(method="Addons.ExecuteAddon",
                    params={'addonid': addonid, 'params': params, 'wait': wait})
    return result


def addons_set_addon_enabled(addonid, enabled=True):
    """
    http://wiki.xbmc.org/?title=JSON-RPC_API/v6#Addons.SetAddonEnabled
    """
    result = exec_rpc(method="Addons.SetAddonEnabled",
                    params={'addonid': addonid, 'enabled': enabled})
    return result
