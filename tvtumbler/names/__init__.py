'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import os
import xbmc

from .. import quality
from ..numbering import SCENE_NUMBERING, TVDB_NUMBERING


__all__ = ['NameParser',
           'SceneNameParser']



class NameParser(object):
    '''
    Base class for all name parsers
    '''

    def __init__(self, filename, has_ext=False, numbering_system=SCENE_NUMBERING):
        '''
        XTor.

        @param filename: (str) Filename (or torrent, link, etc.) to parse.
        @param has_ext: (bool) Set this if filename has an extension (which will be trimmed-off before parsing)
        @param numbering_system: (int) The numbering system used: either SCENE_NUMBERING, or TVDB_NUMBERING.
        '''
        self._parsed = False
        self._known = False
        self._filename = filename
        self._episodes = None
        self._extra_info = None
        self._release_group = None
        self._quality = quality.UNKNOWN_QUALITY
        # self._air_date = None
        self._numbering_system = numbering_system
        self._has_ext = has_ext

    def _parse(self):
        '''
        Override this in derived classes.
        Set _parsed to True (to indicate that parse has been attempted).
        Set _known to True if the parse was successful.
        Set _bad to True if the name is on a blacklist of some sort.
        '''
        self._parsed = True
        self._known = False
        self._bad = False

    @property
    def is_known(self):
        '''
        Return True if the filename was parsed successfully and one or more
        known TvEpisode's were found.  False otherwise.

        @return: (bool)
        '''
        if not self._parsed:
            self._parse()
        return self._known

    @property
    def is_bad(self):
        '''
        Return True if the filename is blacklisted for some reason.
        (and hence shouldn't be downloaded)

        @rtype: bool
        '''
        if not self._parsed:
            self._parse()
        return self._bad

    @property
    def filename(self):
        '''
        @return: (str)
        '''
        return self._filename

    @property
    def tvshow(self):
        '''
        @return: (TvShow|None)
        '''
        if not self._parsed:
            self._parse()
        if len(self._episodes):
            # if we have any episodes, use the TvShow from the first entry
            return self._episodes[0].tvshow
        return None

    @property
    def episodes(self):
        '''
        Get a list of TvEpisode's that have been gleaned from the filename.
        List will be empty if none were found/known.

        @return: ([TvEpisode])
        '''
        if not self._parsed:
            self._parse()
        return self._episodes

    @property
    def extra_info(self):
        '''
        @return: (str|None)
        '''
        if not self._parsed:
            self._parse()
        return self._extra_info

    @property
    def release_group(self):
        '''
        @return: (str|None)
        '''
        if not self._parsed:
            self._parse()
        return self._release_group

    @property
    def quality(self):
        '''
        @return: (int)
        '''
        if not self._parsed:
            self._parse()
        return self._quality

#     @property
#     def air_date(self):
#         '''
#         @return: datetime.date|None
#         '''
#         if not self._parsed: self._parse()
#         return self._air_date

    def make_local_filename(self, numbering=TVDB_NUMBERING):
        '''
        Returns a string like: Show Name - SXXEXX - Episode Name
        **INCLUDES AN EXTENSION if the original filename had one**

        See here for some formats: http://scenenotice.org/details.php?id=2081
        '''
        if not self._parsed:
            self._parse()
        if not self._known:
            # not parseable?  No option but to use the original filename
            return self.filename

        if self._has_ext:
            extension = os.path.splitext(self.filename)[1]
        else:
            extension = ''

        epis = []
        for e in self.episodes:
            if numbering == TVDB_NUMBERING:
                epis.extend(e.tvdb_episodes)
            elif numbering == SCENE_NUMBERING:
                epis.extend(e.scene_episodes)
            else:
                raise Exception('Unknown numbering system: ' + str(numbering))

        epis = list(set(epis))  # remove dups
        epis.sort()  # and sort them

        seasons = set()
        for s, e in epis:
            seasons.add(s)

        # does it span seasons?
        is_multi_season = len(seasons)

        # does it have more than one episode?
        is_multi_episode = len(epis)

        if is_multi_season:
            # Multi season - we have no option here but to list season and episode
            # for each epi.
            # S01E02 - S01E03 - S01E04
            episode_part = ' - '.join(['S%02dE%02d' % e for e in epis])
        else:
            if is_multi_episode:
                # single season, multi episode
                season = epis[0][0]
                epnums = set([e[1] for e in epis])
                is_sequential = (max(epnums) - min(epnums) == len(epnums) - 1)

                if is_sequential:
                    episode_part = 'S%02dE%02d-%02d' % (season, min(epnums), max(epnums))
                else:
                    # not sequential, we need to list them individually
                    # S01E02E03
                    episode_part = 'S%02d' % (season,) + ''.join(['E%02d' % (epi[1],) for epi in epis])
            else:
                # single episode - simplest case
                episode_part = 'S%02dE%02d' % epis[0]

        episode_names = ' & '.join([e.title for e in self.episodes])
        filename = self.tvshow.name + ' - ' + episode_part + ' - ' + episode_names + extension
        return "".join(i for i in filename if i not in r'\/:*?"<>|')



# class BBCNameParser(NameParser):
#    pass

from scene import SceneNameParser
