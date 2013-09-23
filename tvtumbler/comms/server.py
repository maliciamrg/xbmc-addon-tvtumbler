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

from . import common
from .. import logger, tv, quality, log
from ..downloaders import get_enabled_downloaders


__addon__ = sys.modules["__main__"].__addon__


# from .. import events
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
            s = tv.TvShow.from_tvdbd_id(tvdb_id)
            d = {}
            for p in properties:
                d[p] = getattr(s, p)
            l.append(d)
        return l

    def set_show_followed(self, tvdb_id, followed):
        '''Flag a show as followed/ignored'''
        oldvalue = tv.TvShow.from_tvdbd_id(tvdb_id).followed
        show = tv.TvShow.from_tvdbd_id(tvdb_id)
        show.followed = followed
        if show.wanted_quality == 0:
            # ensure that the quality is a valid value
            show.wanted_quality = quality.SD_COMP
        return oldvalue

    def get_show_wanted_quality(self, tvdb_id):
        '''Get the current wanted_quality for a show'''
        return tv.TvShow.from_tvdbd_id(tvdb_id).wanted_quality

    def set_show_wanted_quality(self, tvdb_id, wanted_quality):
        '''Set the wanted_quality for a show'''
        show = tv.TvShow.from_tvdbd_id(tvdb_id)
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
                        d[k] = dl.downloadable.feeder.get_name()
                    elif k == 'downloader':
                        d[k] = dl.downloader.get_name()
                    else:
                        logger.notice('Attempt to get unknown property ' + k)
                result.append(d)
        return result

    def get_non_running_downloads(self, properties=['rowid', 'key', 'name', 'final_status', 'total_size',
                                                 'start_time', 'finish_time', 'source', 'quality'], limit=30):
        return log.get_non_running_downloads(properties, limit)

service_api = Service()


def _handle_message(msg):
    logger.debug('Got message: ' + repr(msg))
    result = {'error': False}
    method = msg['method']
    args = msg['parameters']
    try:
        fn = getattr(service_api, method)
        if not fn:
            raise Exception('Method %s not implemented' % (method,))
        logger.debug('args are ' + repr(args))
        result['result'] = fn(**args) if args is not None else fn()
    except Exception, e:
        logger.error('Error calling Service: ' + str(e))
        logger.error(traceback.format_exc())
        result['error'] = True
        result['errorMessage'] = str(e)
    return result

_socket = None


def run_server():
    global _socket
    if _socket:
        logger.warning('_socket is already set, not starting a new server')
        return

    # we run our socket code in its own thread so that it doesn't block this call
    thread = threading.Thread(target=_socket_server, name='tvtumbler.comms.server')
    thread.start()


# def force_stop():
#     logger.debug('force_stop()')
#     from . import client
#     client.send_shutdown()


def _socket_server():
    global _socket
    socket_details = common.get_socket_details()
    if sys.platform == 'win32':
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    else:
        if xbmcvfs.exists(socket_details):
            logger.debug('Removing stale socket: ' + socket_details)
            xbmcvfs.delete(socket_details)

        _socket = socket.socket(socket.AF_UNIX)

    _socket.bind(socket_details)
    _socket.listen(5)  # allow 5 waiting connections
    _socket.setblocking(0)

    # events.add_event_listener(events.ABORT_REQUESTED, force_stop)

    shutdown_sock = False
    idle_since = time.time()
    waiting = 0
    deep_sleep_secs = 3
    while not shutdown_sock and not xbmc.abortRequested:
        if waiting == 0:
            logger.debug('accepting')
            waiting = 1

        try:
            conn, addr = _socket.accept()  # @UnusedVariable
            if waiting == 2:  # i.e. we were in deep sleep
                logger.debug('waking up, slept for %f secs' % (time.time() - idle_since))
            waiting = 0
        except socket.error, e:
            # these are not 'real' exceptions, they effectively mean no data
            if e.errno == 11 or e.errno == 10035 or e.errno == 35:
                if time.time() - idle_since > deep_sleep_secs:
                    # if we've been waiting longer than deep_sleep_secs,
                    # fall back to an xbmc.sleep for a while
                    xbmc.sleep(500)
                    waiting = 2
                continue  # back to the start of the loop

            # If we're here, we've had a 'real' exception
            logger.error("EXCEPTION : " + repr(e))
        except:
            pass

        if waiting:
            logger.debug("Continue : " + repr(waiting))
            continue

        msg = common.recv(conn)

        # Special handling for the 'SHUTDOWN' message.
        if msg == 'SHUTDOWN':
            logger.debug('Received SHUTDOWN message, setting main.shutdownRequested')
            from .. import main
            main.shutdownRequested = True
            shutdown_sock = True
            try:
                common.send(conn, 'OK')
            except:
                # just ignore an error here, we're shutting down, so it doesn't matter
                pass
        else:
            # This is the 'normal' message handling.
            response = _handle_message(msg)
            try:
                common.send(conn, response)
            except socket.error, e:
                if e.errno == 32:  # broken pipe
                    logger.notice('Error %s when sending response, assuming client timeout' % (repr(e)))
                else:
                    logger.error('Error sending response: ' + repr(e))
                    logger.error(traceback.format_exc())
                    # just fall through and list for new, there's nothing else we can do anyway.

        idle_since = time.time()
        logger.debug('done')

    logger.debug('closing down')
    # _socket.shutdown(_socket.SHUT_RDWR) # not needed, and only works for TCP sockets anyway
    _socket.close()
    if not sys.platform == "win32":
        if xbmcvfs.exists(socket_details):
            logger.debug("Deleting socket file: " + socket_details)
            xbmcvfs.delete(socket_details)

    _socket = None
