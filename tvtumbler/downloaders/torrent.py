'''
This file is part of TvTumbler.

Created on Aug 30, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import base
from .. import links, logger


class TorrentDownloader(base.BaseDownloader):
    '''Base class for all downloaders that do torrents'''

    @classmethod
    def can_download(cls, downloadable):
        '''
        Can this downloader download this downloadable?

        @return: True/False.  Generally a decision made on the class of downloadable.
        @rtype: bool
        '''
        return isinstance(downloadable, links.Torrent)

    def download(self, downloadable):
        '''
        Override in your derived class.
        Be sure to add the 'Download' to _running_downloads.

        @param downloadable: What we want to download.
        @type downloadable: Downloadable
        @return: Boolean value indicating success.
        @rtype: bool
        '''
        rd = TorrentDownload(downloadable, self)
        key = rd.key
        if key in self._running_downloads:
            logger.notice('%s is already downloading!' % (key,))
            return False
        if rd.start():
            self._running_downloads[key] = rd
            return True
        return False


class TorrentDownload(base.Download):

    def get_upload_speed(self):
        '''
        In bytes/sec

        @rtype: float
        '''
        return 0.0
