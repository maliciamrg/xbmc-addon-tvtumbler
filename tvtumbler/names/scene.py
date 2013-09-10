'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import re
from threading import Lock
import time

from unidecode import unidecode
import xbmc

from . import NameParser
from .. import db, jsonrpc, logger, quality, utils, api, events
from ..numbering import SCENE_NUMBERING
from ..tv import TvShow, TvEpisode
from .scene_regexes import get_regexes, get_bad_regexes


class SceneNameParser(NameParser):
    '''
    A parser for Scene Names.
    Most of this is robbed from sickbeard.
    '''

    @classmethod
    def clean_series_name(cls, series_name):
        """Cleans up series name by removing any . and _
        characters, along with any trailing hyphens.

        Is basically equivalent to replacing all _ and . with a
        space, but handles decimal numbers in string, for example:

        >>> cleanRegexedSeriesName("an.example.1.0.test")
        'an example 1.0 test'
        >>> cleanRegexedSeriesName("an_example_1.0_test")
        'an example 1.0 test'

        Stolen from dbr's tvnamer

        @param series_name: (str)
        @return: (str)
        """

        series_name = re.sub("(\D)\.(?!\s)(\D)", "\\1 \\2", series_name)
        series_name = re.sub("(\d)\.(\d{4})", "\\1 \\2", series_name)  # if it ends in a year then don't keep the dot
        series_name = re.sub("(\D)\.(?!\s)", "\\1 ", series_name)
        series_name = re.sub("\.(?!\s)(\D)", " \\1", series_name)
        series_name = series_name.replace("_", " ")
        series_name = re.sub("-$", "", series_name)
        return series_name.strip()

    @classmethod
    def _convert_number(cls, number):
        if type(number) == int:
            return number

        # good lord I'm lazy
        if number.lower() == 'i': return 1
        if number.lower() == 'ii': return 2
        if number.lower() == 'iii': return 3
        if number.lower() == 'iv': return 4
        if number.lower() == 'v': return 5
        if number.lower() == 'vi': return 6
        if number.lower() == 'vii': return 7
        if number.lower() == 'viii': return 8
        if number.lower() == 'ix': return 9
        if number.lower() == 'x': return 10
        if number.lower() == 'xi': return 11
        if number.lower() == 'xii': return 12
        if number.lower() == 'xiii': return 13
        if number.lower() == 'xiv': return 14
        if number.lower() == 'xv': return 15
        if number.lower() == 'xvi': return 16
        if number.lower() == 'xvii': return 17
        if number.lower() == 'xviii': return 18
        if number.lower() == 'xix': return 19
        if number.lower() == 'xx': return 20
        if number.lower() == 'xxi': return 21
        if number.lower() == 'xxii': return 22
        if number.lower() == 'xxiii': return 23
        if number.lower() == 'xxiv': return 24
        if number.lower() == 'xxv': return 25
        if number.lower() == 'xxvi': return 26
        if number.lower() == 'xxvii': return 27
        if number.lower() == 'xxviii': return 28
        if number.lower() == 'xxix': return 29

        return int(number)

    def _parse(self):
        '''
        Parse the filename provided in the xtor.

        Set _parsed to True (to indicate that parse has been attempted)
        and _known to True if the parse was successful.
        '''
        self._parsed = True
        self._known = False  # set this later when we know if have a good match

        if not self._filename:
            return None

        self._quality = quality.quality_from_name(self._filename,
                                                  guess_from_extension=self._has_ext)

        if self._has_ext:
            ext_match = re.match('(.*)\.\w{3,4}$', self._filename)
            if ext_match and self._filename:
                file_name = ext_match.group(1)
            else:
                file_name = self._filename
        else:
            file_name = self._filename

        for (cur_regex_name, cur_regex) in get_regexes():
            match = cur_regex.match(file_name)

            if not match:
                continue

            named_groups = match.groupdict().keys()
            tmp_tv_show = None

            if 'series_name' in named_groups:
                tmp_series_name = self.clean_series_name(match.group('series_name'))
                tvdb_id = get_tvdb_id(tmp_series_name)
                if tvdb_id:
                    tmp_tv_show = TvShow.from_tvdbd_id(tvdb_id)
                    if tmp_tv_show is None:
                        # not a show we know locally
                        return
                else:
                    logger.debug(u'TV Show "%s" not known' % (tmp_series_name,))
                    return
            else:
                # this is really a bug with the regex
                logger.notice(u'Matched on regex %s, but with no series name -> failing' % (cur_regex_name,))
                return

            if 'season_num' in named_groups and 'ep_num' in named_groups:
                tmp_season = match.group('season_num')
                if cur_regex_name == 'bare' and tmp_season in ('19', '20'):
                    continue
                if cur_regex_name == 'mvgroup' and tmp_season is None:
                    tmp_season = '1'
                season_number = int(tmp_season)

                ep_num = self._convert_number(match.group('ep_num'))
                if 'extra_ep_num' in named_groups and match.group('extra_ep_num'):
                    episode_numbers = range(ep_num, self._convert_number(match.group('extra_ep_num')) + 1)
                else:
                    episode_numbers = [ep_num]

                self._episodes = []
                for ep in episode_numbers:
                    if self._numbering_system == SCENE_NUMBERING:
                        self._episodes.extend(TvEpisode.from_scene(tvdb_id=tmp_tv_show.tvdb_id,
                                                                   scene_season=season_number,
                                                                   scene_episode=ep))
                    else:
                        self._episodes.extend(TvEpisode.from_tvdb(tvdb_id=tmp_tv_show.tvdb_id,
                                                                  tvdb_season=season_number,
                                                                  tvdb_episode=ep))
            else:
                if 'air_year' in named_groups and 'air_month' in named_groups and 'air_day' in named_groups:
                    logger.debug('"%s" matched on abd, but we do not support that yet, sorry' %
                                 (self._filename,))
                return

            # Everything from here on is a nice-to-have
            self._known = True

            bad_check_pieces = []  # This is a list of things we check against the bad regex

            if 'extra_info' in named_groups:
                self._extra_info = match.group('extra_info')
                if self._extra_info:
                    bad_check_pieces.append(self._extra_info)

            if 'release_group' in named_groups:
                self._release_group = match.group('release_group')
                if self._release_group:
                    bad_check_pieces.append(self._release_group)

            self._bad = False
            if bad_check_pieces:
                # logger.debug(cur_regex_name)
                # logger.debug(self._filename)
                # logger.debug(repr(bad_check_pieces))
                check_string = '-'.join(bad_check_pieces)
                for rx in get_bad_regexes():
                    if rx.match(check_string):
                        logger.info(u'"%s" matched againstk %s, marking as bad' %
                                    (check_string, rx.pattern))
                        self._bad = True
                        break

            return


SCENE_NAME_REFRESH_INTERVAL_SECS = 60 * 60 * 24
_last_refresh_timestamp = 0


def _get_db():
    _db = db.Connection()
    try:
        dummy = _get_db._init_done
    except:
        _db.action('CREATE TABLE if not exists scene_names '
                   '(exception_id INTEGER PRIMARY KEY, '
                   'tvdb_id INTEGER KEY, show_name TEXT, '
                   'simplified_name TEXT)')
        _get_db._init_done = True
    return _db


def get_scene_names(tvdb_id):
    """
    Given a tvdb_id, return a list of all the scene names.
    """
    if not tvdb_id:
        return []

    _update_if_needed()

    return [x["show_name"] for x in _get_db().select('SELECT show_name '
                                                     'FROM scene_names '
                                                     'WHERE tvdb_id = ?',
                                                     [tvdb_id])]

_scene_name_lookup_cache = {}
_scene_name_lookup_cache_lock = Lock()


def flush_scene_name_lookup_cache():
    global _scene_name_lookup_cache, _scene_name_lookup_cache_lock
    with _scene_name_lookup_cache_lock:
        logger.debug('flushing _scene_name_lookup_cache')
        _scene_name_lookup_cache = {}

events.add_event_listener(events.VIDEO_LIBRARY_UPDATED, flush_scene_name_lookup_cache)
events.add_event_listener(events.EXCEPTIONS_CHANGED, flush_scene_name_lookup_cache)


def get_tvdb_id(scene_name):
    """
    Given a show name, return the tvdbid of the show.

    Matches first against shows known to xbmc, then against exceptions.
    Returns the tvdb_id if a match is found, None if no scene name
    match is present.

    @param scene_name: (str|unicode) show name to match
    @return: (int|None) returns an int on success, None on failure.
    """
    global _scene_name_lookup_cache, _scene_name_lookup_cache_lock
    if scene_name is None:
        return None

    if scene_name in _scene_name_lookup_cache:
        return _scene_name_lookup_cache[scene_name]

    # Simplify the name first
    if not isinstance(scene_name, unicode):
        # We assume utf-8
        scene_name = unicode(scene_name, 'utf-8')

    simplified = simplify_show_name(scene_name)

    # start by comparing it to what we have in xbmc
    known_shows = jsonrpc.get_tv_shows(properties=["title", "imdbnumber"])
    show_matches = [s for s in known_shows if
                    simplify_show_name(s['title']) == simplified]
    if show_matches:
        result = int(show_matches[0]['imdbnumber'])
        with _scene_name_lookup_cache_lock:
            _scene_name_lookup_cache[scene_name] = result
        return result

    _update_if_needed()

    # No match in xbmc names?  Continue with the scene exceptions
    myDB = _get_db()

    # try the obvious case first
    result = myDB.select(u'SELECT tvdb_id FROM scene_names '
                         u'WHERE simplified_name = ?',
                         [simplified])
    if result:
        result = int(result[0]["tvdb_id"])
        with _scene_name_lookup_cache_lock:
            _scene_name_lookup_cache[scene_name] = result
        return result

    # No match?  We fail
    with _scene_name_lookup_cache_lock:
        _scene_name_lookup_cache[scene_name] = None
    return None


def simplify_show_name(showName):
    '''

    @param showName: (unicode) Show name to be simplified.  Must be unicode.
    @return: (str)
    '''
    # Replace '&' with 'and'
    showName = showName.replace('&', 'and')
    # Replace any unicode chars with their nearest ascii equivalents
    showName = unidecode(showName)
    # strip chars that don't generally appear in scene naming
    bad_chars = u",:()'!?\u2019"
    for x in bad_chars:
        showName = showName.replace(x, "")
    # make it lowercase
    showName = showName.lower()
    # remove all whitespace (yes, even in the middle) - makes searching much
    # more reliable
    showName = re.sub('\s+', '', showName)
    return showName


def _update_scene_names():
    """
    """
    exception_dict = api.exceptions()
    if not exception_dict:
        return False

    myDB = _get_db()
    changed_exceptions = False

    # write all the exceptions we got off the net into the database
    for cur_tvdb_id in exception_dict:

        # get a list of the existing exceptions for this ID
        existing_exceptions = [x["show_name"] for x in
                               myDB.select('SELECT * FROM scene_names '
                                           'WHERE tvdb_id = ?',
                                           [cur_tvdb_id])]

        for cur_exception in exception_dict[cur_tvdb_id]:
            # if this exception isn't already in the DB then add it
            if cur_exception not in existing_exceptions:
                logger.debug(u'Adding name %s: %s' % (cur_tvdb_id,
                                                      cur_exception))
                myDB.action('INSERT INTO scene_names ('
                            'tvdb_id, '
                            'show_name, '
                            'simplified_name) '
                            'VALUES (?,?,?)',
                            [cur_tvdb_id,
                             cur_exception,
                             simplify_show_name(cur_exception)])
                changed_exceptions = True

        # check for any exceptions which have been deleted
        for cur_exception in existing_exceptions:
            if cur_exception not in exception_dict[cur_tvdb_id]:
                logger.debug(u'Removing name %s: %s' % (cur_tvdb_id,
                                                        cur_exception))
                myDB.action('DELETE FROM scene_names '
                            'WHERE tvdb_id = ? AND show_name = ?',
                            [cur_tvdb_id, cur_exception])
                changed_exceptions = True

    # since this could invalidate the results of the cache we clear it out
    # after updating
    if changed_exceptions:
        logger.info(u"Updated scene exceptions")
        events.ParentMonitor.onExceptionsChanged()
        # name_cache.clearCache() @todo
    else:
        logger.debug(u"No scene exceptions update needed")

    return True


def _update_if_needed():
    global _last_refresh_timestamp, SCENE_NAME_REFRESH_INTERVAL_SECS
    if (time.time() - _last_refresh_timestamp >
            SCENE_NAME_REFRESH_INTERVAL_SECS and not xbmc.abortRequested):
        _last_refresh_timestamp = time.time()
        _update_scene_names()
