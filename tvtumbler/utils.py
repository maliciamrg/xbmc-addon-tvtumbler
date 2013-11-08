'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import os
import platform
import re
import sys
import threading
import time
import urllib
import uuid

import requests  # @UnresolvedImport
import xbmc
import xbmcvfs

from . import logger, jsonrpc


__addon__ = sys.modules["__main__"].__addon__
__addonname__ = __addon__.getAddonInfo('name')
__addonversion__ = __addon__.getAddonInfo('version')

INSTANCE_ID = str(uuid.uuid1())
_user_agent = None


def is_video_file(filename):
    '''Identify if filename is a video file by its extension.

    @rtype: bool
    '''
    filename = filename.lower()
    if (re.search('(^|[\W_])sample\d*[\W_]', filename) or  # ignore samples
        filename.startswith('._') or  # ignore max osx special files
        '.partial.' in filename):  # ignore iplayer partials
        return False

    # xbmc can also play a bunch of stuff that we don't necessarily want here.
    for bad_ext in ['strm', 'pls', 'm3u', 'm3u8', 'rar', '001', 'zip', 'sdp', 'url', 'rss', 'html']:
        if filename.endswith('.' + bad_ext):
            return False

    return filename.rpartition(".")[2] in get_video_extensions()


def get_video_extensions():
    '''Get the video extensions supported by xbmc.

    @return: a lowercase list of media extensions that xbmc claims to support (extensions only, no dots).
    @rtype: [str]
    '''
    try:
        return get_video_extensions._supported
    except AttributeError:
        get_video_extensions._supported = [ext.lstrip('.').lower()
                                           for ext in xbmc.getSupportedMedia('video').split('|')]
        logger.debug('supported video extensions are: ' + repr(get_video_extensions._supported))
        return get_video_extensions._supported


def get_url(url):
    headers = {'User-Agent': get_user_agent()}
    r = requests.get(url, headers=headers)
    if r.status_code != requests.codes.ok:
        logger.notice('Bad status from %s, status code %d' % (url, r.status_code))
        return None

    return r.text


def get_url_as_json(url):
    headers = {'User-Agent': get_user_agent()}
    r = requests.get(url, headers=headers)
    if r.status_code != requests.codes.ok:
        logger.notice('Bad status from %s, status code %d' % (url, r.status_code))
        return None

    try:
        json_obj = r.json()
    except Exception, e:
        logger.warning(u"%s failed to parse json response: %s" % (url, str(e)))
        return None

    return json_obj


def get_url_as_binary(url):
    headers = {'User-Agent': get_user_agent()}
    r = requests.get(url, headers=headers)
    if r.status_code != requests.codes.ok:
        logger.notice('Bad status from %s, status code %d' % (url, r.status_code))
        return None

    return r.content


def get_user_agent():
    global _user_agent
    if not _user_agent:
        xv = jsonrpc.application_get_properties()
        try:
            pl_sys = platform.system()
            pl_rel = platform.release()
        except Exception, e:
            logger.error('Failure getting system or release (no need to post bugs about this, '
                         'it can be safely ignored): ' + str(e))
            pl_sys = 'Unknown'
            pl_rel = 'Unknown'
        # logger.debug(repr(xv))
        _user_agent = ('%s/%s (%s; %s; %s) %s/%d.%dr%s-%s' % (__addonname__, __addonversion__,
                                                              pl_sys, pl_rel, INSTANCE_ID,
                                                              xv['name'],
                                                              xv['version']['major'], xv['version']['minor'],
                                                              xv['version']['revision'], xv['version']['tag']
                                                              ))
    return _user_agent


def copy_with_timeout(src, dest, timeout=60 * 15):
    '''Performs a xbmcvfs.copy(), but with a timeout.
 
    @param src: Source file path
    @type src: str
    @param dest: Destination file path
    @type dest: str
    @param timeout: Timeout in seconds 
    @type timeout: float
    @rtype: bool
    '''
    if xbmcvfs.exists(dest):
        logger.info('destination already exists, deleting ' + str(dest))
        xbmcvfs.delete(dest)

    start_time = time.time()
    _abort_copy_operation = False
    _retList = [False]

    def _copy_func(retList):
        source_file = xbmcvfs.File(src)
        dest_file = xbmcvfs.File(dest, 'w')
        filesize = source_file.size()
        copied = 0
        last_reported = 0

        while copied < filesize:
            if (xbmc.abortRequested or
                time.time() > (start_time + timeout) or
                _abort_copy_operation):
                logger.warning('timeout or abort.  quiting file copy at %d bytes' % (copied,))
                source_file.close()
                dest_file.close()
                retList[0] = False # this is our return value
                return
            block = source_file.read(1024 * 1024)
            dest_file.write(block)
            copied += len(block)
            if copied - last_reported >= 10 * 1024 * 1024:
                logger.debug('copied %d bytes of %d in %s' % (copied, filesize, src))
                last_reported = copied

        source_file.close()
        dest_file.close()
        retList[0] = True  # this is out return value

    copyThread = threading.Thread(target=_copy_func, args=(_retList,))
    copyThread.start()
    while copyThread.is_alive() and time.time() < (start_time + timeout):
        xbmc.sleep(500)

    if copyThread.is_alive():
        logger.warning('copy_with_timeout has timed-out.  Going to try to kill the thread')
        _abort_copy_operation = True
        copyThread.join(5)  # give the script 5 secs to stop
        if copyThread.is_alive():
            logger.error('Failed to stop the copy thread.  Abandoning.')
        return False

    return _retList[0]  # this will be either True or False, depending on file copy success

