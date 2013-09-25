'''
This file is part of TvTumbler.

Created on Sep 10, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import socket
import sys
import traceback
import os
import xbmc

from . import common
from .. import logger, jsonrpc


__addon__ = sys.modules["__main__"].__addon__


class ServerNotRunningException(Exception):
    pass


class Client(object):
    '''
    This serves as a way of directly communicating between user-interactive code
    (i.e. the video or program script) and non-interactive code (the service), which
    run in separate python instances and would normally have no way of calling one
    another.

    To use it somewhere in your code:
    >>> from tvtumbler.comms.client import service_api
    >>> result = service_api.some_method(some_param)

    This will call `some_method` in tvtumbler.comms.server.Service passing it `some_param`
    and return whatever it returns.  The only restriction on params (and return values) is
    that they be pickleable.

    As a means of test, there's an `echo` method in Service, which will simply return
    what you pass it:
    >>> service_api.echo('this is a nice little test message')
    'this is a nice little test message'

    '''
    def __getattr__(self, key):
        try:
            return object.__getattr__(self, key)
        except AttributeError:
            def function(*args, **kwargs):
                # print("You tried to call a method named: %s" % (key,))
                # logger.debug(repr(kwargs))
                result = send_message(method=key, params=kwargs)
                if result['error']:
                    if 'serverNotRunning' in result and result['serverNotRunning']:
                        raise ServerNotRunningException(result['errorMessage'])
                    raise Exception(result['errorMessage'])
                else:
                    return result['result']
            return function

    def stop_service(self):
        try:
            logger.debug('Telling the old server (if any) to shut down (any errors can be safely ignored)')
            _send_raw('SHUTDOWN')
            xbmc.sleep(5000)
        except Exception, e:
            logger.info('Shutdown got error: ' + str(e))

        logger.debug('... done')

    def start_service(self):
        try:
            logger.debug('Telling the server to start up')

            # See this stuff??  None of it works!
            # (they all either try to start the gui, or crash xbmc)

            # service_path = os.path.join(__addon__.getAddonInfo('path').decode('utf-8'), 'service.py')
            # xbmc.executebuiltin('XBMC.AlarmClock(StartTvTumbler, XBMC.RunScript(%s), 00:00:03, true)' % (service_path,))
            # xbmc.executebuiltin('XBMC.RunScript(%s)' % (service_path))
            # xbmc.executebuiltin('XBMC.RunAddon(%s)' % (__addon__.getAddonInfo('id')))
            # xbmc.executescript(service_path)
            #jsonrpc.addons_execute_addon(__addon__.getAddonInfo('id'))

            # The only way that I can currently find to do this safely is to disable and then
            # enable the addon:
            logger.debug('DISABLING %s' % (__addon__.getAddonInfo('id'),))
            jsonrpc.addons_set_addon_enabled(__addon__.getAddonInfo('id'), enabled=False)
            xbmc.sleep(1000)
            logger.debug('ENABLING %s' % (__addon__.getAddonInfo('id'),))
            jsonrpc.addons_set_addon_enabled(__addon__.getAddonInfo('id'), enabled=True)
            xbmc.sleep(5000)  # give it 5 seconds to start
        except Exception, e:
            logger.error('Failure starting the service: ' + str(e))
            logger.error(traceback.format_exc())
            return False

        return True

    def restart_service(self):
        # start is actually a restart, so use it instead
        return self.start_service()

    def get_client_version(self):
        return __addon__.getAddonInfo('version')

#     def check_available(self, start_if_needed=False):
#         '''Check if the service is available (i.e the server end of this code is running and has the correct
#         version).
#
#         IMPORTANT: For now, start_if_needed causes Gotham to crash (at least on OSX).  So best not to use it.
#
#         @param start_if_needed: If set, an attempt will be made to start the service if it's not running (or restart
#             it if the version number it's giving is wrong.
#         @return: True if the service is available and has the same version as the client, False otherwise.
#         @rtype: bool
#         '''
#         server_vers_result = send_message(method='get_version')
#         server_version = server_vers_result['result'] if not server_vers_result['error'] else 'Unknown'
#         client_version = __addon__.getAddonInfo('version')
#         logger.debug('Client version: "%s", Server version: "%s"' % (client_version, server_version))
#         if client_version == server_version:
#             logger.debug('Server running, and versions match.  Available.')
#             return True  # nothing to do in this instance
#         elif start_if_needed:
#             if not self.restart_service():
#                 return False
#
#             # Try asking the server version again:
#             server_vers_result = send_message(method='get_version')
#             server_version = server_vers_result['result'] if not server_vers_result['error'] else 'Unknown'
#             logger.debug('Client version: "%s", Server version is now: "%s"' % (client_version, server_version))
#             return client_version == server_version
#         else:
#             return False


service_api = Client()


def _send_raw(raw_data):
    socket_details = common.get_socket_details()
    if sys.platform == 'win32':
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        s.connect(socket_details)
        common.send(s, raw_data)

        # wait for data back.
        msg = common.recv(s)
        s.close()
        return msg
    except socket.error, e:
        result = {'error': True}
        if e.errno in [111, 2]:
            result['errorMessage'] = 'Failed to connect, server not running?'
            result['serverNotRunning'] = True
        else:
            result['errorMessage'] = repr(e)
        logger.error('socket.error: ' + str(e))
        logger.error(traceback.format_exc())
        return result


def send_message(method, params=None):
    return _send_raw({'method': method, 'parameters': params})


# def send_shutdown():
#     return _send_raw('SHUTDOWN')
