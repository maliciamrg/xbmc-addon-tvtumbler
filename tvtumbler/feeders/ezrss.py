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
        self.rss_url = 'http://www.ezrss.it/feed/'

    @classmethod
    def is_available(cls):
        return True

    @classmethod
    def is_enabled(cls):
        return (__addon__.getSetting('ezrss_enable') == 'true')
