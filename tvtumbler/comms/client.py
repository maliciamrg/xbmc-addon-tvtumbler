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

from . import common


class Client(object):
    '''
    This serves as a way of directly communicating between user-interactive code
    (i.e. the video or program script) and non-interactive code (the service), which
    run in separate python instances and would normally have no way to calling one
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
                    raise Exception(result['errorMessage'])
                else:
                    return result['result']
            return function

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
        if e.errno in [111]:
            result['errorMessage'] = 'Failed to connect, server not running?'
        else:
            result['errorMessage'] = repr(e)
        return result


def send_message(method, params=None):
    return _send_raw({'method': method, 'parameters': params})


# def send_shutdown():
#     return _send_raw('SHUTDOWN')
