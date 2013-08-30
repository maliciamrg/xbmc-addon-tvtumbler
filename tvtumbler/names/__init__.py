'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

__all__ = ['NameParser',
           'SceneNameParser']

from ..numbering import SCENE_NUMBERING
from .. import quality


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
        Set _parsed to True (to indicate that parse has been attempted)
        and _known to True if the parse was successful.
        '''
        self._parsed = True
        self._known = False

    @property
    def is_known(self):
        '''
        Return True if the filename was parsed successfully and one or more
        known TvEpisode's were found.  False otherwise.

        @return: (bool)
        '''
        if not self._parsed: self._parse()
        return self._known

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
        if not self._parsed: self._parse()
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
        if not self._parsed: self._parse()
        return self._episodes

    @property
    def extra_info(self):
        '''
        @return: (str|None)
        '''
        if not self._parsed: self._parse()
        return self._extra_info

    @property
    def release_group(self):
        '''
        @return: (str|None)
        '''
        if not self._parsed: self._parse()
        return self._release_group

    @property
    def quality(self):
        '''
        @return: (int)
        '''
        if not self._parsed: self._parse()
        return self._quality

#     @property
#     def air_date(self):
#         '''
#         @return: datetime.date|None
#         '''
#         if not self._parsed: self._parse()
#         return self._air_date

from scene import SceneNameParser

# class BBCNameParser(NameParser):
#    pass
