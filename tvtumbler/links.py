'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

from . import logger, quality
import datetime
import hashlib
import re
import base64


class Downloadable(object):
    '''Base class for all remote, download-able, links.'''

    def __init__(self, urls, episodes, name=None, quality=quality.UNKNOWN_QUALITY,
                 timestamp=datetime.datetime.now(), feeder=None):
        '''
        XTor

        @param urls: ([str]) a list of strings, each one being a link to the downloadable
        @param episodes: ([TvEpisode]) a list of TvEpisodes, promised by this Downloadable
        @param name: (str) Optional name - informational only
        @param quality: (int) One of the predefined quality constants.  See tvtumbler.quality.
        @param timestamp: (datetime.datetime) Timestamp when this item became available
        @param feeder: (tvtumbler.feeders.base.BaseFeeder) Optional feeder that supplied the downloadable.
        '''
        self._urls = urls
        self._episodes = episodes
        self._name = name
        self._quality = quality
        self._timestamp = timestamp
        self._feeder = feeder

    def __repr__(self):
        return self.__class__.__name__ + '(urls=%s, episodes=%s, name=%s, quality=%s, timestamp=%s, feeder=%s)' % (
                    repr(self._urls),
                    repr(self._episodes),
                    repr(self._name),
                    ('\'' + quality.quality_strings[self._quality] + '\'') if self._quality is not None else 'None',
                    repr(self._timestamp),
                    repr(self._feeder),
                )

    @property
    def urls(self):
        '''
        @return: ([str])
        '''
        return self._urls

    @property
    def episodes(self):
        '''
        @return: ([Downloadabe])
        '''
        return self._episodes

    @property
    def name(self):
        '''
        @return: (str)
        '''
        return self._name

    @property
    def timestamp(self):
        '''
        @return: (datetime.datetime)
        '''
        return self._timestamp

    @property
    def feeder(self):
        '''
        @return: (tvtumbler.feeders.base.BaseFeeder)
        '''
        return self._feeder

    def _get_quality(self):
        '''
        @return: (int) One of the predefined quality values (see tvtumbler.quality)
        '''
        return self._quality

    def _set_quality(self, new_quality):
        '''
        @param new_quality: (int) Set a new quality.  Must be a valid quality from tvtumbler.quality, otherwise
            it will be ignored.
        '''
        if new_quality & quality.ANY:
            self._quality = new_quality
        else:
            logger.notice('Attempt to set invalid quality value: ' + str(new_quality))

    quality = property(_get_quality, _set_quality)

    def is_newer_than(self, ts):
        '''
        @param ts: (datetime.datetime)
        @return (bool)
        '''
        return self._timestamp > ts

    def get_preferred_url(self, **kwargs):
        '''
        Here we just return the first uri, but subclasses can make better choices
        based on the arguments provided.

        @return: (str)
        '''
        return self._urls[0]

    def __str__(self):
        return self.name

    @property
    def tvshow(self):
        '''
        @rtype: TvEpisode
        '''
        if len(self._episodes):
            return self._episodes[0].tvshow
        else:
            return None

    @property
    def is_wanted(self):
        for ep in self._episodes:
            if ep.is_wanted_in_quality(self.quality):
                return True
        return False

    @property
    def unique_key(self):
        '''
        Get a key (a string) which is unique to this downloadable.
        Preferably this should be unique to the url (so that duplicates can be detected).
        The default implementation here just returns an md5 of the preferred url.

        @return: Unique Key for Downloadable
        @rtype: str
        '''
        return hashlib.md5(self.get_preferred_url()).hexdigest()


class Torrent(Downloadable):
    '''A torrent link'''

    def _get_infohash(self):
        '''
        Getting for infohash property
        '''
        try:
            return self._infohash
        except AttributeError:
            # don't have it already?  See if we can get it from one of the urls
            for u in [ux for ux in self._urls if ux.startswith('magnet:')]:
                h = self.get_hash_from_magnet(u)
                if h:
                    self._infohash = h
                    return h
            # don't have a working magnet?  Then try a hail mary for one of
            # the cache links
            for u in [ux for ux in self.urls if ux.startswith('http')]:
                h = self.get_hash_from_cache_link(u)
                if h:
                    self._infohash = h
                    return h
        return None

    def _set_infohash(self, infohash):
        '''
        Setter for infohash property.

        @param infohash:
        @type infohash: str
        '''
        self._infohash = infohash

    infohash = property(_get_infohash, _set_infohash, None, 'The infohash for the torrent (if available)')

    def get_magnet(self):
        for u in self._urls:
            if u.startswith('magnet:'):
                return u
        # no native magnet in urls?  Make one
        h = self._get_infohash()
        if h:
            return 'magnet:?xt=urn:btih:' + h

        return None

    @staticmethod
    def get_hash_from_magnet(magnet):
        """
        Pull the hash from a magnet link (if possible).
        Handles the various possible encodings etc.
        (returning a 40 byte hex string).

        Returns None on failure
        """
        logger.debug('magnet: ' + magnet)
        info_hash_search = re.search('btih:([0-9A-Z]+)', magnet, re.I)
        if info_hash_search:
            torrent_hash = info_hash_search.group(1)

            # hex hashes will be 40 characters long, base32 will be 32 chars long
            if len(torrent_hash) == 32:
                # convert the base32 to base 16
                logger.debug('base32_hash: ' + torrent_hash)
                torrent_hash = base64.b16encode(base64.b32decode(torrent_hash, True))
            elif len(torrent_hash) != 40:
                logger.debug('Torrent hash length (%d) is incorrect (should be 40)' % (len(torrent_hash)))
                return None

            logger.debug('torrent_hash: ' + torrent_hash)
            return torrent_hash.upper()
        else:
            # failed to pull info hash
            return None

    # This is a list of sites that serve torrent files given the associated hash.
    # They will be tried in order, so put the most reliable at the top.
    MAGNET_TO_TORRENT_URLS = ['http://torrage.com/torrent/%s.torrent',
                              'http://zoink.it/torrent/%s.torrent',
                              'http://torcache.net/torrent/%s.torrent',
                              'http://torra.ws/torrent/%s.torrent',
                              'http://torrage.ws/torrent/%s.torrent',
                             ]

    @classmethod
    def get_hash_from_cache_link(cls, link):
        """
        Pulls the hash of a torrent from a link to an online torrent cache site
        (typically one of MAGNET_TO_TORRENT_URLS).

        Returns the 40 byte hex string on success, None on failure.
        """
        for m_to_u in cls.MAGNET_TO_TORRENT_URLS:
            m_to_u.replace('%%s', '([0-9A-Z]{40})', re.I)
            hash_search = re.search(m_to_u, link)
            if hash_search:
                return hash_search.group(1).upper()

        return None

    @property
    def unique_key(self):
        '''
        Will return the infohash if available, otherwise falls back to the parent implementation

        @return: Unique Key for Downloadable
        @rtype: str
        '''
        try:
            return self._unique_key
        except AttributeError:
            ih = self.infohash
            if ih:
                self._unique_key = ih
                return ih

        return super(Torrent, self).unique_key()


class VOD(Downloadable):
    '''A download-able video-on-demand link'''
    pass
