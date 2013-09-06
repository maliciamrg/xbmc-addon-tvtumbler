'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import re
import sys

from .. import quality
from .base import TorrentFeeder


__addon__ = sys.modules["__main__"].__addon__


class PublicHDFeeder(TorrentFeeder):

    def __init__(self):
        super(PublicHDFeeder, self).__init__()
        self.rss_url = 'http://publichd.se/rss.php'

    @classmethod
    def is_available(cls):
        return True

    @classmethod
    def is_enabled(cls):
        return (__addon__.getSetting('publichd_enable') == 'true')

    def _parse_rss_item(self, item):
        '''
        RSS item (from _parse_rss_feed) to Torrent.

        @param item: (dict)
        @return: (Torrent|None) If the item does not have any known TvEpisodes, return None.
        '''
        if item.title.startswith('[TORRENT] '):
            item.title = item.title[10:]

        crudAtEndMatch = re.match(r'(.*) \[\w+\]$', item.title)
        if crudAtEndMatch:
            item.title = crudAtEndMatch.group(1)

        torrent = super(PublicHDFeeder, self)._parse_rss_item(item)

        return torrent

    def _is_valid_category(self, item):
        """
        Decides if the category of an item (from the rss feed) could be a valid
        tv show.
        @param item: (dict)
        @return: boolean
        """
        return item.category in ('BluRay 720p', 'BluRay 1080p', 'BluRay Remux',
                            'BluRay', 'BluRay 3D', 'XviD', 'BRRip',
                            'HDTV', 'SDTV', 'TV WEB-DL', 'TV Packs')
