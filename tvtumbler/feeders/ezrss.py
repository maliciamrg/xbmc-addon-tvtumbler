'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import sys

from .base import TorrentFeeder


__addon__ = sys.modules["__main__"].__addon__


class EZRSSFeeder(TorrentFeeder):

    def __init__(self):
        super(EZRSSFeeder, self).__init__()
        self.rss_url = ['http://www.ezrss.it/feed/',
                        'https://rss.thepiratebay.sx/user/d17c6a45441ce0bc0c057f19057f95e1',
                        'http://www.ezrss.it.nyud.net/feed/',
                        'http://show-api.tvtumbler.com/api/ezrss-mirror',
                        ]

    @property
    def update_freq_secs(self):
        return 60 * int(__addon__.getSetting('ezrss_freq'))

    @classmethod
    def is_available(cls):
        return True

    @classmethod
    def is_enabled(cls):
        return (__addon__.getSetting('ezrss_enable') == 'true')

    @classmethod
    def get_name(cls):
        '''
        @retur: Human-readable name.
        @rtype: str
        '''
        return 'EZRSS'
