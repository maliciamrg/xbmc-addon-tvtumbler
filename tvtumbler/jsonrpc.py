'''
Created on Jun 21, 2013

@author: dermot
'''
import sys
import xbmc
import tvtumbler.logger as logger

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json
    

def exec_rpc(method, params=None):
    command = {
        'method': method,
        'id': id,
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


def get_tv_shows(properties=["title", "year", "imdbnumber", "file"]):
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#VideoLibrary.GetTVShows
    """
    result = exec_rpc(method="VideoLibrary.GetTVShows",
                    params={'properties': properties})
    return result['tvshows']


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
    return exec_rpc(method="VideoLibrary.GetEpisodes",
                    params={'tvshowid': tvshowid,
                            'season': season,
                            'properties': properties})


def get_episode_details(episodeid,
                        properties=['title', 'season', 'episode', 'file', 
                                    'tvshowid']):
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#VideoLibrary.GetEpisodeDetails
    """
    return exec_rpc(method="VideoLibrary.GetEpisodeDetails",
                    params={'episodeid': episodeid,
                            'properties': properties})


def videolibrary_scan(directory=""):
    """
    http://wiki.xbmc.org/index.php?title=JSON-RPC_API/v6#VideoLibrary.Scan
    """
    return exec_rpc(method="VideoLibrary.Scan",
                    params={'directory': directory})

