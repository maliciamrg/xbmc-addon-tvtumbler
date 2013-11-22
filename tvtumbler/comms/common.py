'''
This file is part of TvTumbler.

Created on Sep 10, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import cPickle
import os
import socket
import struct
import sys

import xbmc

from .. import logger


COMMS_PORT = 28574


# def get_socket_details():
#     if sys.platform == 'win32':
#         logger.debug('Running under windows, using tcp sockets')
#         socket_details = ('127.0.0.1', COMMS_PORT)  # '' => localhost
#     else:
#         logger.debug('Running under posix')
#         socket_details = os.path.join(xbmc.translatePath('special://temp/').decode('utf-8'), 'tvtumbler.sock')
#
#     return socket_details
#
#
# def send(sock, data):
#     data = cPickle.dumps(data)
#     datasize = len(data)
#     sock.send(struct.pack("=Q", datasize))
#     datasent = sock.send(data)
#     dataleft = datasize - datasent
#     count = 0
#     while dataleft > 0 and count < 10:
#         xbmc.sleep(10)
#         data = data[datasent:]
#         datasent = sock.send(data)
#         dataleft = dataleft - datasent
#         count = count + 1
#     if count > 9:
#         raise Exception('Failed to send all data, remaining data is: ' . data[datasent:])
#
#
# def recv(sock):
#     count = 0
#     while count < 10:
#         try:
#             datasize = struct.unpack("=Q", sock.recv(8))[0]
#             break
#         except socket.error, e:
#             if count == 10:
#                 raise Exception('Timeout waiting for data')
#             if e.errno == 11 or e.errno == 10035 or e.errno == 35:
#                 xbmc.sleep(50)
#                 count = count + 1
#                 continue
#             raise e
#     rcvd_bytes = 0
#     data = ''
#     count = 0
#     while count < 10:
#         try:
#             rcvd_chunk = sock.recv(datasize)
#         except socket.error, e:
#             if e.errno == 11 or e.errno == 10035 or e.errno == 35:
#                 xbmc.sleep(50)
#                 count = count + 1
#                 continue
#             raise e
#         data = data + rcvd_chunk
#         rcvd_bytes = rcvd_bytes + len(rcvd_chunk)
#         if rcvd_bytes >= datasize:
#             break
#         count = count + 1
#         xbmc.sleep(10)
#     if count == 10:
#         raise Exception('Timeout waiting for data')
#
#     pick = cPickle.loads(data)
#     return pick
