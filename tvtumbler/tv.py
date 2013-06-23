'''
Created on Jun 21, 2013

@author: dermot
'''

import tvtumbler.jsonrpc as jsonrpc
import tvtumbler.thetvdb as thetvdb
import tvtumbler.logger as logger


class TvShow(object):

    """
    A TvShow
    """

    def __init__(self, tvshowid, name=None, tvdb_id=None, path=None):
        '''
        Constructor.

        @param tvshowid: (int)
        @param name: (str)
        @param tvdb_id: (str)
        @param path: (str)
        '''
        self._tvshowid = tvshowid
        self._name = name
        self._imdbnumber = tvdb_id  # actually, this seems to be the tvdb_id
        self._path = path

    @classmethod
    def from_tvdbd_id(cls, tvdb_id):
        shows = jsonrpc.get_tv_shows()
        show_matches = [s for s in shows if s['imdbnumber'] == tvdb_id]
        if show_matches:
            s = show_matches[0]
            return cls(tvshowid=s['tvshowid'],
                       name=s['title'],
                       tvdb_id=s['tvdb_id'],
                       path=s['file'])
        else:
            # no match locally?  try tvdb
            s = thetvdb.tvdb_series_lookup(tvdb_id)
            if s:
                return cls(tvshowid=None,
                           name=s['SeriesName'],
                           tvdb_id=tvdb_id,
                           path=None)
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
            self._get_xbmc_details()
        return self._name

    @property
    def tvdb_id(self):
        """
        Read-only property: tvdb_id
        """
        if self._imdbnumber is None:
            self._get_xbmc_details()

        return self._imdbnumber

    def _get_xbmc_details(self):
        tvshowdetails = jsonrpc.get_tv_show_details(self._tvshowid,
                                        ['title', 'imdbnumber', 'file'])
        self._name = tvshowdetails['title']
        self._imdbnumber = tvshowdetails['imdbnumber']
        self._path = tvshowdetails['file']


class TvEpisode(object):

    """
    An episode of a TvShow
    """

    def __init__(self, episodeid=None, tvshow=None,
                 x_season=None, x_episode=None,
                 sc_season=None, sc_episode=None):
        '''
        Constructor.
        
        Supply all the information you have.  Other data will be populated
        as needed (provided the necessary pieces of the puzzle are there!)
        
        @param episodeid: (int) xbmc episodeid (if known)
        @param tvshow: (int|TvShow) xbmc tvshowid, or an instance of TvShow
        @param x_season: (int) xbmc season number.  Use zero for specials.
        @param x_episode: (int) xbmc episode number.
        @param sc_season: (int) scene season number.  Use zero for specials.
        @param sc_episode: (int) scene episode number.
        '''
        self._episodeid = episodeid
        if tvshow is None:
            self._tvshow = None
        elif isinstance(tvshow, TvShow):
            self._tvshow = tvshow
        else:  # otherwise we assume that tvshow is a tvshowid
            self._tvshow = TvShow(tvshowid=tvshow)

        self._x_season = x_season
        self._x_episode = x_episode
        self._sc_season = sc_season
        self._sc_episode = sc_episode



