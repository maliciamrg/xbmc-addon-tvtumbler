'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import sys

from .. import quality
from .base import TorrentFeeder


__addon__ = sys.modules["__main__"].__addon__


class ShowRSSFeeder(TorrentFeeder):

    def __init__(self):
        super(ShowRSSFeeder, self).__init__()
        self.rss_url = 'http://showrss.karmorra.info/feeds/all.rss'

    @classmethod
    def is_available(cls):
        return True

    @classmethod
    def is_enabled(cls):
        return (__addon__.getSetting('showrss_enable') == 'true')

    def _parse_rss_item(self, item):
        '''
        RSS item (from _parse_rss_feed) to Torrent.

        @param item: (dict)
        @return: (Torrent|None) If the item does not have any known TvEpisodes, return None.
        '''
        if item.title.startswith('HD 720p: '):
            item.title = item.title[9:]
            known_quality = quality.HD720P_COMP
        else:
            known_quality = False
        torrent = super(ShowRSSFeeder, self)._parse_rss_item(item)
        if torrent and torrent.quality == quality.UNKNOWN_QUALITY and known_quality:
            torrent.quality = known_quality
        return torrent
