'''
This file is part of TvTumbler.

Created on Aug 30, 2013

http://www.rasterbar.com/products/libtorrent/manual.html

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
from .torrent import TorrentDownlaoder, TorrentDownload
from .. import logger

LIBTORRENT_AVAILABLE = False
LIBTORRENT_FAILURE_REASON = None
try:
    import libtorrent as lt
    if (lt.version_major, lt.version_minor) < (0, 16):
        LIBTORRENT_FAILURE_REASON = (u'The version of libtorrent you have installed '
                                     u'"%s", is too old for use with tvtumbler.  '
                                     u'Version 0.16 or later required.') % (lt.version,)
        logger.notice(LIBTORRENT_FAILURE_REASON)
    else:
        logger.notice('libtorrent import succeeded, libtorrent is available')
        LIBTORRENT_AVAILABLE = True
except ImportError:
    LIBTORRENT_FAILURE_REASON = 'libtorrent import failed, functionality will not be available'
    logger.notice(LIBTORRENT_FAILURE_REASON)


class LibtorrentDownloader(TorrentDownloader):
    def __init__(self):
        super(TorrentDownloader, self).__init__()
        # @todo: set up session

    @classmethod
    def is_available(cls):
        '''
        Is this downloader available?
        (i.e. could it operate if enabled)

        @rtype: bool
        '''
        return LIBTORRENT_AVAILABLE

    @classmethod
    def is_enabled(cls):
        '''
        Is this downloader enabled?
        (i.e. willing to accept downloads)

        @rtype: bool
        '''
        # @todo: this should be a config thing
        return True

    def add(self, downloadable):
        rd = TorrentDownload(downloadable)
        self._running_downloads[rd.key] = rd

    def remove(self, key):
        del self._running_downloads[key]
