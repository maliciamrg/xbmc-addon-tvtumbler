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
from .. import logger, tv, quality


# from .. import events
class Service(object):
    '''
    This is the server portion of the comms between gui and service.
    See the comments in tvtumbler.comms.client.Client for details.
    '''
    def echo(self, text):
        '''Simple test method which just echos the first parameter'''
        return text

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
        result['result'] = fn(**args)
    except Exception, e:
        logger.error('Error calling Service: ' + str(e))
        logger.debug(traceback.format_exc())
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

        # Special handling for the 'SHUTDOWN' message.  Actually, not required
        # any longer since we use non-blocking io, but no reason to remove it yet.
        if msg == 'SHUTDOWN':
            shutdown_sock = True
            common.send(conn, 'OK')
        else:
            response = _handle_message(msg)
            common.send(conn, response)

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
