'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import time, datetime
import feedparser  # @UnresolvedImport

from .. import logger
from ..names import SceneNameParser
from ..links import Downloadable, Torrent
from ..numbering import SCENE_NUMBERING


class BaseFeeder(object):
    """Base class for all feeders"""

    def __init__(self):

        # e.g. http://example.com/rss
        self.rss_url = None

        # Cache of latest entries (a list of Downloadable's)
        self._latest = []

        # timestamp of last update
        self._last_update_timestamp = None

    @property
    def update_freq_secs(self):
        return 15 * 60  # our default is 15 minutes

    @classmethod
    def get_instance(cls):
        '''Get the singleton instance of this class

        @return: The singleton instance of this class
        @rtype: cls
        '''
        try:
            return cls._instance
        except AttributeError:
            cls._instance = cls()
            return cls._instance

    @classmethod
    def get_name(cls):
        '''
        Human-readable name.
        @return: (str)
        '''
        return cls.__name__

    @classmethod
    def get_nameparser(cls):
        '''
        Which name parser is to be used for this feeder.

        @return: (type) A class inheriting from NameParser.
        '''
        return SceneNameParser

    @classmethod
    def get_numbering(cls):
        '''
        Which numbering system does this feeder use.

        @return: (int) Currently only SCENE_NUMBERING and TVDB_NUMBERING
            are supported.
        '''
        return SCENE_NUMBERING

    def is_update_due(self):
        return (self._last_update_timestamp is None or
                self._last_update_timestamp + self.update_freq_secs < time.time())

    def get_latest(self):
        '''
        Return a list of available downloads.
        Will call update() if needed.

        @return: ([Downloadable]) A list of Downloadable's
        '''
        if self.is_update_due():
            self._update()

        return self._latest

    def _update(self):
        '''
        '''
        if isinstance(self.rss_url, basestring):
            urls = [self.rss_url, ]
        else:
            urls = self.rss_url

        self._last_update_timestamp = time.time()
        self._latest = []

        for rss_url in urls:
            feed = feedparser.parse(rss_url)
            if feed:
                for entry in feed.entries:
                    i = self._parse_rss_item(entry)
                    if i:
                        if i.is_blacklisted():
                            logger.debug('Ignoring this downloadable, it has been blacklisted: ' + repr(i))
                        else:
                            self._latest.append(i)
                return True
        return False

    def _parse_rss_item(self, item):
        '''
        RSS item (from _parse_rss_feed) to Downloadable.
        Override this in derived classes to return the correct type of Downloadable.

        @param item: (dict)
        @return: (Downloadable|None) If the item does not have any known TvEpisodes, return None.
        '''
        return None

    @classmethod
    def is_available(cls):
        '''
        Is this feeder available?
        (i.e. could it operate if enabled)

        @rtype: bool
        '''
        return False

    @classmethod
    def is_enabled(cls):
        '''
        Is this feeder enabled?
        (i.e. in the config)

        @rtype: bool
        '''
        return False


class TorrentFeeder(BaseFeeder):
    """Base class for all feeders that supply torrents"""

    def _parse_rss_item(self, item):
        '''
        RSS item (from _parse_rss_feed) to Torrent.

        @param item: (dict)
        @return: (Torrent|None) If the item does not have any known TvEpisodes, return None.
        '''
        fileName = None
        title = None
        pubDate = None
        urls = []
        infoHash = None

        # logger.debug(repr(item))
        # logger.debug(repr(item.enclosures))

        try:
            fileName = item.filename
        except (KeyError, AttributeError):
            pass

        try:
            magnet_uri = item.magneturi
            if magnet_uri:
                urls.append(magnet_uri)
        except (KeyError, AttributeError):
            pass

        try:
            for enc in item.enclosures:
                if (enc.type == 'application/x-bittorrent' or
                    enc.href.startswith('magnet:') or
                    enc.href.endwidth('.torrent')):
                    urls.append(enc.href)
        except (KeyError, AttributeError):
            pass

        try:
            for link in item.links:
                if link.href.startswith('magnet:') or link.href.endswith('.torrent'):
                    urls.append(link.href)
        except (KeyError, AttributeError):
            pass

        try:
            title = item.title
        except (KeyError, AttributeError):
            pass

        try:
            pubDate = item.published_parsed
        except (KeyError, AttributeError), e:
            logger.debug('unable to parse date, using current timestamp instead:' + str(e))
            pubDate = datetime.datetime.now()

        try:
            infoHash = item.infohash
            if infoHash:
                magnets = [k for k in urls if k.startswith('magnet:')]
                if len(magnets) == 0:
                    # If we have no magnet, but we have the infoHash, then make a magnet
                    urls.append('magnet:?xt=urn:btih:' + infoHash)
        except (KeyError, AttributeError):
            pass

        # remove any duplicate urls
        urls = list(set(urls))

        if len(urls) == 0:
            logger.debug(u'No useful links found in item')
            return None

        if fileName:
            # If we have the fileName, use that for the name parser
            parse_name = fileName
            has_ext = True
        else:
            # Otherwise, we must use the title
            parse_name = title
            has_ext = False

        nameparser = self.get_nameparser()(parse_name, has_ext=has_ext,
                                           numbering_system=self.get_numbering())

        if not nameparser.is_known:
            # Not parsable?  Fail
            return None

        return Torrent(urls=urls,
                    episodes=nameparser.episodes,
                    name=title,
                    quality=nameparser.quality,
                    timestamp=pubDate,
                    feeder=self)


class VODFeeder(BaseFeeder):
    """Base class for all feeders that supply video-on-demand"""
    pass
