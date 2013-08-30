'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

from .base import TorrentFeeder


class EZRSSFeeder(TorrentFeeder):

    def __init__(self):
        super(EZRSSFeeder, self).__init__()
        self.rss_url = 'http://www.ezrss.it/feed/'
