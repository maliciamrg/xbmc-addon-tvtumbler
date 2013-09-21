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

    @classmethod
    def get_download_class(cls):
        return TorrentDownload


class TorrentDownload(base.Download):

    def get_upload_speed(self):
        '''
        In bytes/sec

        @rtype: float
        '''
        return 0.0

    def get_uploaded_size(self):
        '''In bytes.

        @rtype: int
        '''
        return 0

    def get_ratio(self):
        dled = self.get_downloaded_size()
        uped = self.get_uploaded_size()
        if dled:
            return uped / dled
        else:
            return None

