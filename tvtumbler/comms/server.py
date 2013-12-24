'''
This file is part of TvTumbler.

A very, very, simple socket server.

Created on Sep 10, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import socket
import sys
import threading
import time
import traceback

import xbmc
import xbmcvfs
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

from . import common
from .. import logger, tv, quality, log, thetvdb, epdb, events
from ..downloaders import get_enabled_downloaders, is_downloading


__addon__ = sys.modules["__main__"].__addon__


class Service(object):
    '''
    This is the server portion of the comms between gui and service.
    See the comments in tvtumbler.comms.client.Client for details.
    '''
    def echo(self, text):
        '''Simple test method which just echoes the first parameter'''
        return text

    def get_version(self):
        '''Get __addonversion__'''
        return __addon__.getAddonInfo('version')

    def get_all_shows(self, properties=['tvshowid', 'name', 'tvdb_id', 'followed', 'wanted_quality', 'fanart',
                                        'thumbnail', 'poster', 'banner']):
        '''Return a list of all shows (both in the xbmc library, and in the database)'''
        l = []
        for s in tv.TvShow.get_all_shows():
            d = {}
            for p in properties:
                d[p] = getattr(s, p)
            l.append(d)
        return l

    def get_shows(self, tvdb_ids, properties=['tvshowid', 'name', 'tvdb_id', 'followed', 'wanted_quality', 'fanart',
                                        'thumbnail', 'poster', 'banner']):
        '''Return a list of dicts with the properties of the shows with the tvdb_ids given.'''
        l = []
        for tvdb_id in tvdb_ids:
            s = tv.TvShow.from_tvdb_id(tvdb_id)
            d = {}
            for p in properties:
                d[p] = getattr(s, p)
            l.append(d)
        return l

    def set_show_followed(self, tvdb_id, followed):
        '''Flag a show as followed/ignored'''
        oldvalue = tv.TvShow.from_tvdb_id(tvdb_id).followed
        show = tv.TvShow.from_tvdb_id(tvdb_id)
        show.followed = followed
        if show.wanted_quality == 0:
            # ensure that the quality is a valid value
            show.wanted_quality = quality.SD_COMP
        return oldvalue

    def get_show_wanted_quality(self, tvdb_id):
        '''Get the current wanted_quality for a show'''
        return tv.TvShow.from_tvdb_id(tvdb_id).wanted_quality

    def set_show_wanted_quality(self, tvdb_id, wanted_quality):
        '''Set the wanted_quality for a show'''
        show = tv.TvShow.from_tvdb_id(tvdb_id)
        oldvalue = show.wanted_quality
        show.wanted_quality = wanted_quality
        return oldvalue

    def get_running_downloads(self, properties=['rowid', 'key', 'name', 'status', 'status_text', 'total_size',
                                                'downloaded_size', 'download_speed', 'start_time', 'source',
                                                'downloader'],
                              sort_by='start_time'):
        result = []
        for dler in get_enabled_downloaders():
            for dl in dler.downloads:
                d = dict()
                for k in properties:
                    # these ones are properties (we can read them straight)
                    if k in ['rowid', 'key', 'name', 'total_size', 'start_time']:
                        d[k] = getattr(dl, k, None)
                    elif k == 'status':
                        d[k] = dl.get_status()
                    elif k == 'status_text':
                        d[k] = dl.get_status_text()
                    elif k == 'downloaded_size':
                        d[k] = dl.get_downloaded_size()
                    elif k == 'download_speed':
                        d[k] = dl.get_download_speed()
                    elif k == 'source':
                        d[k] = dl.downloadable.feeder.get_name() if dl.downloadable.feeder else ''
                    elif k == 'downloader':
                        d[k] = dl.downloader.get_name()
                    else:
                        logger.notice('Attempt to get unknown property ' + k)
                result.append(d)
        return result

    def get_non_running_downloads(self, properties=['rowid', 'key', 'name', 'final_status', 'total_size',
                                                 'start_time', 'finish_time', 'source', 'quality'], limit=30):
        return log.get_non_running_downloads(properties, limit)

    def search_series_by_name(self, searchstring):
        return thetvdb.search_series_by_name(searchstring)

    def add_show(self, tvdb_id, followed=True, wanted_quality=quality.SD_COMP):
        show = tv.TvShow.from_tvdb_id(tvdb_id)
        show.followed = followed
        show.wanted_quality = wanted_quality
        return True

    def get_episodes_on_date(self, firstaired, properties=['episodeid', 'tvdb_season', 'tvdb_episode', 'title',
                                                           'art', 'show_fanart', 'show_thumbnail',
                                                           'show_tvdb_id', 'show_name',  # 'show_status',
                                                           # 'fanart', 'thumbnail',
                                                           # 'show_banner', 'show_fanart', 'show_thumbnail', 'show_poster',
                                                           'have_state',
                                                           ]):
        '''

        @param firstaired: Date to check.  A string in iso date format (yyyy-mm-dd)
        @type firstaired: str
        @param properties:
        @type properties: [str]
        @return: a list of episodes (each a dict) with the required properties that first aired on that date.
        @rtype: [{}]
        '''
        eps = epdb.get_episodes_on_date(firstaired)
        result = []
        for ep in eps:
            for t_ep in ep.tvdb_episodes:  # this is actually a list of tuples [season, episode]
                d = dict()
                for k in properties:
                    if k in ['episodeid', 'title', 'fanart', 'thumbnail', 'art', 'firstaired']:
                        d[k] = getattr(ep, k, None)
                    elif k == 'tvdb_season':
                        d[k] = t_ep[0]
                    elif k == 'tvdb_episode':
                        d[k] = t_ep[1]
                    elif k == 'show_tvdb_id':
                        d[k] = ep.tvshow.tvdb_id
                    elif k == 'show_name':
                        d[k] = ep.tvshow.name
                    elif k == 'show_status':
                        d[k] = ep.tvshow.status
                    elif k == 'show_banner':
                        d[k] = ep.tvshow.banner
                    elif k == 'show_fanart':
                        d[k] = ep.tvshow.fanart
                    elif k == 'show_thumbnail':
                        d[k] = ep.tvshow.thumbnail
                    elif k == 'show_poster':
                        d[k] = ep.tvshow.poster
                    elif k == 'have_state':
                        if ep.episodeid:
                            d[k] = 'downloaded'
                        elif is_downloading(ep):
                            d[k] = 'downloading'
                        else:
                            d[k] = 'missing'
                    else:
                        logger.notice('Attempt to get unknown property: ' + str(k))
                result.append(d)
        return result

    def get_seasons(self, tvdb_id):
        '''Get a list of seasons for this show (a list of ints)'''
        # logger.debug('get_seasons: ' + repr(tvdb_id))
        # logger.debug('ssss')
        s = tv.TvShow.from_tvdb_id(tvdb_id)
        logger.debug(repr(s))
        return s.get_seasons()

    def get_episodes_in_season(self, tvdb_id, tvdb_season, properties=['episodeid', 'tvdb_season', 'tvdb_episode', 'title',
                                                           #'art', 'show_fanart', 'show_thumbnail',
                                                           #'show_tvdb_id', 'show_name',  # 'show_status',
                                                           # 'fanart', 'thumbnail',
                                                           # 'show_banner', 'show_fanart', 'show_thumbnail', 'show_poster',
                                                           'have_state',
                                                           ]):
        '''

        @param tvdb_id: tvdb_id of the show
        @type tvdb_id: int
        @param tvdb_season: season number
        @type tvdb_season: int
        @param properties:
        @type properties: [str]
        @return: a list of episodes (each a dict) with the required properties that first aired on that date.
        @rtype: [{}]
        '''
        show = tv.TvShow.from_tvdb_id(tvdb_id)
        eps = show.get_episodes(tvdb_season)
        result = []
        for ep in eps:
            for t_ep in ep.tvdb_episodes:  # this is actually a list of tuples [season, episode]
                d = dict()
                for k in properties:
                    if k in ['episodeid', 'title', 'fanart', 'thumbnail', 'art', 'firstaired']:
                        d[k] = getattr(ep, k, None)
                    elif k == 'tvdb_season':
                        d[k] = t_ep[0]
                    elif k == 'tvdb_episode':
                        d[k] = t_ep[1]
                    elif k == 'show_tvdb_id':
                        d[k] = ep.tvshow.tvdb_id
                    elif k == 'show_name':
                        d[k] = ep.tvshow.name
                    elif k == 'show_status':
                        d[k] = ep.tvshow.status
                    elif k == 'show_banner':
                        d[k] = ep.tvshow.banner
                    elif k == 'show_fanart':
                        d[k] = ep.tvshow.fanart
                    elif k == 'show_thumbnail':
                        d[k] = ep.tvshow.thumbnail
                    elif k == 'show_poster':
                        d[k] = ep.tvshow.poster
                    elif k == 'have_state':
                        if ep.episodeid:
                            d[k] = 'downloaded'
                        elif is_downloading(ep):
                            d[k] = 'downloading'
                        else:
                            d[k] = 'missing'
                    else:
                        logger.notice('Attempt to get unknown property: ' + str(k))
                result.append(d)
        return result

    def refresh_episodes(self, tvdb_id):
        '''Refresh the episode list for the show tvdb_id'''
        epdb.refresh_show(tvdb_id)
        return True

service_api = Service()

_rpc_server = None


def run_server():
    global _rpc_server
    if _rpc_server:
        logger.warning('_rpc_server is already set, not starting a new server')
        return

    # we run our socket code in its own thread so that it doesn't block this call
    thread = threading.Thread(target=_socket_server, name='tvtumbler.comms.server')
    thread.start()


def _socket_server():
    global _rpc_server

    addr = ('', common.COMMS_PORT)
    _rpc_server = SimpleJSONRPCServer(addr, address_family=socket.AF_INET)
    _rpc_server.register_instance(service_api)
    _rpc_server.serve_forever()


def _stop_server():
    global _rpc_server

    if _rpc_server:
        _rpc_server.shutdown()
        _rpc_server = None

events.add_event_listener(events.ABORT_REQUESTED, _stop_server)
