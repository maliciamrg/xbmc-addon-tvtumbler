'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import os
import sys

from dateutil import parser
import xbmc

from . import jsonrpc, logger, downloaders, api, showsettings, thetvdb, tvrage
from .numbering import xem


__addon__ = sys.modules["__main__"].__addon__


class TvShow(object):

    """
    A TvShow
    """

    def __init__(self, tvshowid, name, tvdb_id, path):
        '''
        Private Constructor.
        Do not use: use one of the from_* class methods instead.

        @param tvshowid: (int)
        @param name: (str)
        @param tvdb_id: (str)
        @param path: (str)
        '''
        self._tvshowid = tvshowid
        self._name = name
        self._imdbnumber = tvdb_id  # actually, this seems to be the tvdb_id
        self._path = path
        self._fanart = None
        self._thumbnail = None
        self._art = None
        self._tvdb_info = None
        self._year = None
        self._tvrage_id = None
        self._country_code = None

    def __repr__(self):
        return self.__class__.__name__ + '(tvshowid=%s, name=%s, tvdb_id=%s, path=%s)' % (
                    repr(self._tvshowid),
                    repr(self._name),
                    repr(self._imdbnumber),
                    repr(self._path),
                )

    def __eq__(self, other):
        if self._tvshowid is not None and other._tvshowid is not None:
            return self._tvshowid == other._tvshowid
        else:
            return self._imdbnumber == other._imdbnumber

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def from_tvdbd_id(cls, tvdb_id):
        '''
        Create an instance of a TvShow from a tvdb_id.
        If the show in known to xbmc, the details will be loaded from there.  If not
        an attempt will be made to load them from thetvdb.  If that fails None will be returned.

        @param tvdb_id: (int)
        @return: (TvShow|None)
        '''
        shows = jsonrpc.get_tv_shows()
        show_matches = [s for s in shows if s['imdbnumber'] == str(tvdb_id)]
        if show_matches:
            s = show_matches[0]
            return cls(tvshowid=s['tvshowid'],
                       name=s['title'],
                       tvdb_id=s['imdbnumber'],
                       path=s['file'] if 'file' in s else None)
        else:
            # no match locally?  try tvdb
            # s = api.show(tvdb_id)
            seriesname = thetvdb.get_tvdb_field(tvdb_id=tvdb_id, key_name='seriesname',
                                       allow_remote_fetch=True)
            if seriesname:
                return cls(tvshowid=None,
                           name=seriesname,
                           tvdb_id=tvdb_id,
                           path=None)
            else:
                return None

    @classmethod
    def from_xbmc(cls, tvshowid):
        '''
        Load a TvShow from xbmc.
        If the show is known (tvshowid is correct), a fully populated TvShow will be returned.
        Otherwise None is returned.

        @param tvshowid: (int)
        @return: (TvShow|None)
        '''
        t = cls(tvshowid=tvshowid, name=None, tvdb_id=None, path=None)
        if t._get_xbmc_details():
            return t
        else:
            return None

    @property
    def tvshowid(self):
        """
        Read-only property: tvshowid
        """
        return self._tvshowid

    @property
    def name(self):
        """
        Read-only property: name
        """
        if self._name is None:
            if self._tvshowid:
                self._get_xbmc_details()
            elif self._imdbnumber:
                show_data = api.show(self._imdbnumber)
                if show_data:
                    self._name = show_data['series_name']
        return self._name

    @property
    def tvdb_id(self):
        """
        Read-only property: tvdb_id
        """
        if self._imdbnumber is None:
            self._get_xbmc_details()

        return self._imdbnumber

    @property
    def tvrage_id(self):
        '''
        @rtype: int
        '''
        if self._tvrage_id is None:
            if self.tvdb_id:
                api_info = api.show(self.tvdb_id)
                if api_info:
                    self._tvrage_id = api_info['tvrage_id']
        return self._tvrage_id

    def get_path(self):
        '''
        Get the full path to the folder containing the show.
        This is a method (rather than a property) because new shows won't
        have a path yet and one will need to deduced.

        @rtype: unicode
        '''
        if self._path:
            return self._path
        else:
            root_dir = xbmc.translatePath(__addon__.getSetting('new_show_path').decode('utf-8'))
            show_dir = xbmc.makeLegalFilename(self.name, False).decode('utf-8')
            logger.debug('root dir = "%s", show_dir = "%s"' % (root_dir, show_dir))
            return os.path.join(root_dir, show_dir)

    def _get_xbmc_details(self):
        '''
        Populate _name, _imdbnumber, and _path from xbmc by lookup on _tvshowid

        @return: (bool) True on successful lookup, False on failure.
        '''
        tvshowdetails = jsonrpc.get_tv_show_details(self._tvshowid,
                                        ['title', 'year', 'imdbnumber', 'file'])
        if tvshowdetails:
            if 'title' in tvshowdetails:
                self._name = tvshowdetails['title']
            if 'imdbnumber' in tvshowdetails:
                self._imdbnumber = tvshowdetails['imdbnumber']
            if 'year' in tvshowdetails:
                try:
                    self._year = int(tvshowdetails['year'])
                except ValueError:
                    pass
            if 'file' in tvshowdetails:
                self._path = tvshowdetails['file']

            return True
        else:
            return False

    def _get_wanted_quality(self):
        '''
        Return the quality we want the episodes in (actually a quality mask).
        Note that this doesn't necessarily mean that we want the episodes, you
        also need to check the `wanted` property.

        @return: The wanted quality for this show.  Returns zero if not wanted.
        @rtype: int
        '''
        row = showsettings.get_show_settings_row(self.tvdb_id)
        if row:
            return int(row['wanted_quality'])
        else:
            return 0  # Not wanted
        # return quality.HD_COMP | quality.SD_COMP

    def _set_wanted_quality(self, wanted_quality):
        showsettings.set_show_settings_row(self.tvdb_id,
                                           follow=None,  # ie. no change to follow flag
                                           wanted_quality=int(wanted_quality))

    wanted_quality = property(fget=_get_wanted_quality, fset=_set_wanted_quality)

    def _get_followed(self):
        '''
        Do we want to download new episodes of the show as they become available?

        @rtype: bool
        '''
        row = showsettings.get_show_settings_row(self.tvdb_id)
        if row:
            return row['follow'] in [1, '1']
        else:
            return False  # Not wanted

    def _set_followed(self, follow):
        showsettings.set_show_settings_row(self.tvdb_id,
                                   follow=1 if follow else 0,
                                   wanted_quality=None)  # None here means no change

    followed = property(fget=_get_followed, fset=_set_followed)

    @property
    def fanart(self):
        if self._fanart is None and self.tvshowid:
            s = jsonrpc.get_tv_show_details(self.tvshowid, properties=['fanart'])
            self._fanart = s['fanart']
        return self._fanart

    @property
    def thumbnail(self):
        if self._thumbnail is None and self.tvshowid:
            s = jsonrpc.get_tv_show_details(self.tvshowid, properties=['thumbnail'])
            self._fanart = s['thumbnail']
        return self._thumbnail

    def _load_art(self):
        if self.tvshowid:
            s = jsonrpc.get_tv_show_details(self.tvshowid, properties=['art'])
            self._art = s['art']
            return True
        return False

    @property
    def poster(self):
        if self._art is None:
            if not self._load_art():
                return None
        return self._art.get('poster', None)

    @property
    def banner(self):
        if self._art is None:
            if not self._load_art():
                return None
        return self._art.get('banner', None)

    @property
    def year(self):
        '''
        Get the first-aired year.  Returns None if unknown.

        @rtype: int
        '''
        if self._year is None:
            first_aired = self._get_tvdb_field('firstaired', allow_remote_fetch=True)
            if first_aired:
                parse_result = parser.parse(first_aired)
                if parse_result:
                    self._year = parse_result.year
        return self._year

    @property
    def country_code(self):
        '''
        Get the origin country (iso3166-alpha2) code.  Returns None if unknown.
        Care here: don't use this needlessly, it can involve several http requests.

        @rtype: str
        '''
        if self._country_code is None:
            show_info = tvrage.tvrage_showinfo(self.tvrage_id)
            if show_info and 'origin_country' in show_info:
                self._country_code = show_info['origin_country']

                # if it truly is a 2-char country code, make it uppercase for consistency
                if len(self._country_code) == 2:
                    self._country_code = self._country_code.upper()

        return self._country_code

    @property
    def status(self):
        '''The status of the show as reported by thetvdb.

        @rtype: str
        '''
        return self._get_tvdb_field('status')

    @property
    def fast_status(self):
        '''Same as status, but will only used cached values.
        Returns None if there is no cached value.
        @rtype: str
        '''
        return self._get_tvdb_field('status', allow_remote_fetch=False)

    def _get_tvdb_field(self, key_name, allow_remote_fetch=True):
        '''
        Get a field from the tvdb_api by name.
        Note that this can be very slow, use with care.
        '''
        return thetvdb.get_tvdb_field(self.tvdb_id, key_name, allow_remote_fetch)

    @classmethod
    def get_followed_shows(cls):
        '''
        Return a list of all wanted TvShows.

        @return: A list of TvShow objects, one for each wanted show.
        @rtype: [TvShow]
        '''
        shows = []
        for tid in showsettings.get_all_tvdb_ids(True):
            shows.append(TvShow.from_tvdbd_id(tid))
        return shows

    @classmethod
    def get_xbmc_shows(cls):
        '''
        Return a list of all shows that are in the library (i.e. have at least one episode).

        @return: A list of TvShow object, one for each show in the library.
        @rtype: [TvShow]
        '''
        return [TvShow.from_xbmc(s['tvshowid']) for s in jsonrpc.get_tv_shows(properties=[])]

    @classmethod
    def get_all_shows(cls):
        '''
        Return a list of all shows we deal with, including:
            all shows that are somehow referenced in the database (even if not followed)
            all shows in the xbmc library

        @return: A list of TvShow objects.  The list will not have duplicates, but will be in random order.
        @rtype: [TvShow]
        '''
        tvdb_ids = set()
        for tid in showsettings.get_all_tvdb_ids(False):
            tvdb_ids.add(int(tid))
        for s in jsonrpc.get_tv_shows(properties=['imdbnumber']):
            tvdb_ids.add(int(s['imdbnumber']))
        return [TvShow.from_tvdbd_id(t) for t in tvdb_ids]


class TvEpisode(object):
    """
    An episode of a TvShow
    """

    def __init__(self, episodeid, tvshow,
                 tvdb_episodes,
                 scene_episodes):
        '''
        Private Constructor.

        Generally best _not_ to use this, use one of the class from_* functions instead.

        @param episodeid: (int) xbmc episodeid (if known)
        @param tvshow: (int|TvShow) xbmc tvshowid, or an instance of TvShow
        @param tvdb_episodes: ([(int, int)]) A list of corresponding tvdb episodes (season, episode), or just a single
            tuple.
        @param scene_episodes: ([(int, int)]) A list of corresponding scene episodes (season, episode), or just a
            single tuple.
        '''
        self._episodeid = episodeid
        if tvshow is None:
            self._tvshow = None
        elif isinstance(tvshow, TvShow):
            self._tvshow = tvshow
        else:  # otherwise we assume that tvshow is a tvshowid
            self._tvshow = TvShow.from_xbmc(tvshowid=tvshow)

        if type(tvdb_episodes) is tuple:
            tvdb_episodes = [tvdb_episodes]

        if type(scene_episodes) is tuple:
            scene_episodes = [scene_episodes]

        self._tvdb_episodes = tvdb_episodes
        self._sc_episodes = scene_episodes
        self._title = None
        self._art = None
        self._thumbnail = None
        self._fanart = None

    def __repr__(self):
        return self.__class__.__name__ + '(episodeid=%s, tvshow=%s, tvdb_episodes=%s, scene_episodes=%s)' % (
                    repr(self._episodeid),
                    repr(self._tvshow),
                    repr(self._tvdb_episodes),
                    repr(self._sc_episodes),
                )

    def __eq__(self, other):
        if self._episodeid is not None and other._episodeid is not None:
            return self._episodeid == other._episodeid
        else:
            return self._tvdb_episodes == other._tvdb_episodes

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def from_xbmc(cls, episodeid):
        '''
        Get a single, fully-populated TvEpisode by supplying its xbmc episodeid

        @param episodeid: (int)
        @return: (TvEpisode)
        '''
        try:
            ep = cls(episodeid=episodeid, tvshow=None, tvdb_episodes=None, scene_episodes=None)
            ep._populate_from_xbmc()
            return ep
        except jsonrpc.JsonRPCException, e:
            if e.code == -32602:
                raise EpisodeNotFoundException('Failure loading episode :"' + str(episodeid) + '"')
            logger.warning('Got an exception while loading an episode by id.  Re-raising')
            raise
        return ep

    @classmethod
    def from_tvdb(cls, tvdb_id, tvdb_season, tvdb_episode):
        '''
        Get a list of matching TvEpisode's by supplying the tvdb_id, and the tvdb season/episode numbers.

        @param tvdb_id: (int)
        @param tvdb_season: (int)
        @param tvdb_episode: (int)
        @return: ([TvEpisode]) Generally only a single list entry will be returned - multiple entries will
            usually only occur if there are multiple matching episodes (files) in the xbmc database.
        '''
        show = TvShow.from_tvdbd_id(tvdb_id)

        # if the show is known to xbmc, we need to check for multiple matching
        # episode entries
        if show.tvshowid:
            eps = cls._get_xbmc_matching_episodes(tvshowid=show.tvshowid,
                                                   tvdb_season=tvdb_season,
                                                   tvdb_episode=tvdb_episode)
            if eps:
                return eps

        ep = cls(episodeid=None, tvshow=show,
                 tvdb_episodes=[(tvdb_season, tvdb_episode)],
                 scene_episodes=None)
        ep._populate_scene_numbering()
        return [ep]

    @classmethod
    def from_scene(cls, tvdb_id, scene_season, scene_episode):
        '''
        Get a list of matching TvEpisode's by supplying the tvdb_id and the scene season/episode numbers.
        This is much the same as from_tvdb(), but assumes scene_numbering.

        @param tvdb_id: (int)
        @param scene_season: (int)
        @param scene_episode: (int)
        @return: ([TvEpisode]) Generally only a single list entry will be returned - multiple entries will
            usually only occur if there are multiple matching episodes (files) in the xbmc database, or
            the scene numbering maps to multiple tvdb episodes (or a combination of both).
        '''
        tvdb_episodes = xem.get_tvdb_numbering_from_xem(tvdb_id=tvdb_id,
                                                   sceneSeason=scene_season,
                                                   sceneEpisode=scene_episode)
        if not tvdb_episodes:
            # No scene episodes from xem?  Use the tvdb ones.
            tvdb_episodes = [(scene_season, scene_episode)]

        notinx_episodes = tvdb_episodes

        show = TvShow.from_tvdbd_id(tvdb_id)
        eps = []

        # If the show is known to xbmc
        if show.tvshowid:
            # we need to check for any existing matches
            for (s, e) in tvdb_episodes:
                eps_in_x = cls._get_xbmc_matching_episodes(show.tvshowid, s, e)
                if eps_in_x:
                    try:
                        # found, stop looking for it
                        notinx_episodes.remove((s, e))
                    except ValueError:
                        pass
                    eps.extend(eps_in_x)

        # pick up any stragglers
        for (s, e) in notinx_episodes:
            ep = cls(episodeid=None, tvshow=show,
                 tvdb_episodes=[(s, e)],
                 scene_episodes=[(scene_season, scene_episode)])
            eps.append(ep)

        return eps

    @classmethod
    def _get_xbmc_matching_episodes(cls, tvshowid, tvdb_season, tvdb_episode):
        '''
        Get a list of episodes with matching season, episode numbering from xbmc.
        Will return multiple matches if there are multiple library entries for an episode.

        @param tvshowid: (int)
        @param tvdb_season: (int)
        @param tvdb_episode: (int)
        @return: [TvEpisode] Returns an empty list for no matches.
        '''
        eps_in_season = jsonrpc.get_episodes(tvshowid=tvshowid, season=int(tvdb_season))
        eps_matching = [e for e in eps_in_season if e['episode'] == int(tvdb_episode)]
        if eps_matching:
            eps = []
            for ep in eps_matching:
                eps.append(TvEpisode.from_xbmc(ep['episodeid']))
            return eps
        else:
            return []

    def _populate_from_xbmc(self, overwrite=False):
        if self._episodeid is None:
            raise ValueError('episodeid needed to populate from xbmc')

        xbmc_data = jsonrpc.get_episode_details(self._episodeid)

        if self._tvshow is None or overwrite:
            self._tvshow = TvShow.from_xbmc(tvshowid=xbmc_data['tvshowid'])

        if self._tvdb_episodes is None or overwrite:
            self._tvdb_episodes = [(xbmc_data['season'], xbmc_data['episode'])]

        if self._sc_episodes is None or overwrite:
            self._populate_scene_numbering()

        if self._title is None or overwrite:
            self._title = xbmc_data['title']

        if self._fanart is None or overwrite:
            self._fanart = xbmc_data['fanart']

        if self._thumbnail is None or overwrite:
            self._thumbnail = xbmc_data['thumbnail']

        if self._art is None or overwrite:
            self._art = xbmc_data['art']

    def _populate_scene_numbering(self):
        if (self._tvshow is None or
            not self._tvdb_episodes):
            raise ValueError('tvshow, season, and episode are needed to get '
                             'scene numbering')

        self._sc_episodes = []
        for (ts, te) in self._tvdb_episodes:
            xem_data = xem.get_scene_numbering_from_xem(self._tvshow.tvdb_id, tvdbSeason=ts, tvdbEpisode=te)

            if xem_data:
                self._sc_episodes.extend(xem_data)
            else:
                # No xem mappings?  Just use tvdb numbering
                self._sc_episodes.extend([(ts, te)])

        self._sc_episodes = list(set(self._sc_episodes))  # remove dups

    @property
    def episodeid(self):
        '''
        This will be set if the episode is in the xbmc library, otherwise it will be None.

        @return: (int|None)
        '''
        return self._episodeid

    @property
    def tvshow(self):
        '''
        @return: (TvShow)
        '''
        return self._tvshow

    @property
    def title(self):
        '''
        @rtype: str
        '''
        if self._title is not None:
            return self._title
        self._title = ' & '.join([thetvdb.get_episode_name(self.tvshow.tvdb_id, s, e) for s, e in self.tvdb_episodes])
        return self._title

    @property
    def fanart(self):
        return self._fanart

    @property
    def thumbnail(self):
        return self._thumbnail

    @property
    def art(self):
        return self._art

    @property
    def tvdb_episodes(self):
        '''
        @return: [(int, int)]
        '''
        return self._tvdb_episodes

    @property
    def scene_episodes(self):
        '''
        @return: [(int, int)]
        '''
        return self._sc_episodes

    def is_wanted_in_quality(self, qual):
        '''
        @todo: FIXME!  This doesn't take into account yet if we have it in one quality, but want it
            in a higher one.

        @param qual: Quality to check against.  One of the constants in quality.py
        @type qual: int
        @return: True if this is an episode we want in a quality we want.  False otherwise.
        @rtype: bool
        '''
        logger.debug('is_wanted_in_quality')
        return (self._tvshow.followed and
                self._tvshow.wanted_quality & qual and
                not self.episodeid and
                not downloaders.is_downloading(self))


class EpisodeNotFoundException(Exception):
    pass
