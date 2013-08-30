'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import datetime
from . import quality
from . import logger


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

class Torrent(Downloadable):
    '''A torrent link'''
    pass


class VOD(Downloadable):
    '''A download-able video-on-demand link'''
    pass
