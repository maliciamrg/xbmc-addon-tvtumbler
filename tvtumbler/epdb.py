'''
This file is part of TvTumbler.

Module for a local tv database.

Created on Sep 25, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import time
from threading import Lock

from tvdb_api import tvdb_api

import xbmc


from . import db, thetvdb, logger
from .tv import TvShow

_episode_lock = Lock()


def _get_db():
    _db = db.Connection()
    try:
        dummy = _get_db._init_done
    except:
        _db.action('CREATE TABLE if not exists episode ('
                   'tvdb_episode_id INTEGER, '
                   'tvdb_id INTEGER, '
                   'seasonid INTEGER, '
                   'seasonnumber INTEGER, '
                   'episodenumber INTEGER, '
                   'absolute_number INTEGER, '
                   'episodename TEXT, '
                   'overview TEXT, '
                   'firstaired TEXT, '
                   'dvd_chapter INTEGER, '
                   'dvd_discid INTEGER, '
                   'dvd_episodenumber REAL, '
                   'dvd_season INTEGER, '
                   'airsafter_season INTEGER, '
                   'airsbefore_episode INTEGER, '
                   'airsbefore_season INTEGER, '
                   'PRIMARY KEY (tvdb_episode_id))')
        _db.action('CREATE TABLE if not exists episode_refresh ('
                              'tvdb_id INTEGER PRIMARY KEY, '
                              'last_refreshed INTEGER)')
        _get_db._init_done = True
    return _db


def get_episode_name(tvdb_id, season, episode):
    db = _get_db()
    rows = db.select('SELECT episodename '
                     'FROM episode '
                     'WHERE tvdb_id = ? '
                     'AND seasonnumber = ? '
                     'AND episodenumber = ?', [tvdb_id, season, episode])
    if rows:
        return int(rows[0]['episodename'])
    else:
        t = thetvdb.get_tvdb_api_info(tvdb_id)
        try:
            return t[season][episode]['episodename']
        except tvdb_api.tvdb_episodenotfound, e:
            logger.error('tvdb_api reported: "' + str(e) + '", using Episode N as the episode name')
            return 'Episode ' + str(episode)


def refresh_needed_shows(cutoff_for_continuing=60 * 60 * 24,
                         cutoff_for_ended=60 * 60 * 24 * 10,
                         show_limit=None):
    '''
    Iterate through all shows and refresh those most in need of a refresh.

    @param cutoff_for_continuing: Cutoff (in seconds) since last refresh for shows with status 'Continuing'
    @type cutoff_for_continuing: int
    @param cutoff_for_ended: Cutoff (in seconds) since last refresh for shows with status 'Ended'
    @type cutoff_for_ended: int
    @param show_limit: Maximum number of shows to refresh.  None = no limit
    @type show_limit: int
    @return: Returns the number of shows refreshed.
    @rtype: int
    '''
    from . import main

    latest_continuing = time.time() - cutoff_for_continuing
    latest_ended = time.time() - cutoff_for_ended

    shows_to_refresh = []  # actually, just store the tvdb_id's and last refresh in here
    for s in TvShow.get_all_shows():
        status = s.fast_status
        last_refreshed = _get_show_last_refreshed(s.tvdb_id)
        if last_refreshed is None:
            last_refreshed = 0  # simpler this way
        if status == 'Continuing' or status is None:
            if last_refreshed < latest_continuing:
                shows_to_refresh.append((s.tvdb_id, last_refreshed))
        else:  # everything else is considered 'Ended'
            if last_refreshed < latest_ended:
                shows_to_refresh.append((s.tvdb_id, last_refreshed))

    # sort the shows_to_refresh by last_refreshed (the second element in each tuple)
    shows_to_refresh.sort(key=lambda x: x[1])
    if show_limit is not None:
        shows_to_refresh = shows_to_refresh[:show_limit]

    for s in shows_to_refresh:
        if xbmc.abortRequested or main.shutdownRequested:
            logger.debug('Shutdown in progress, aborting refresh')
            break
        refresh_show(s[0])

    return len(shows_to_refresh)


def refresh_show(tvdb_id):
    global _episode_lock

    key_map = {'id': 'tvdb_episode_id',
               'seasonid': 'seasonid',
               'absolute_number': 'absolute_number',
               'episodename': 'episodename',
               'overview': 'overview',
               'firstaired': 'firstaired',
               'dvd_chapter': 'dvd_chapter',
               'dvd_discid': 'dvd_discid',
               'dvd_episodenumber': 'dvd_episodenumber',
               'dvd_season': 'dvd_season',
               'airsafter_season': 'airsafter_season',
               'airsbefore_episode': 'airsbefore_episode',
               'airsbefore_season': 'airsbefore_season'}

    t = thetvdb.get_tvdb_api_info(tvdb_id)
    _db = _get_db()

    for season_num in t:
        sqls = []  # we do our updates in bulk on the season level
        for episode_num in t[season_num]:
            ep = t[season_num][episode_num]
            data = {'tvdb_id': tvdb_id,
                    'seasonnumber': season_num,
                    'episodenumber': episode_num}
            for key in key_map:
                if key in ep:
                    data[key_map[key]] = ep[key]
            sql = 'INSERT INTO episode (' + ', '.join(data.keys()) + ') VALUES (' + ', '.join('?' * len(data)) + ')'
            sqls.append((sql, data.values()))

        with _episode_lock:
            _db.action('DELETE FROM episode WHERE tvdb_id = ? AND seasonnumber = ?', [tvdb_id, season_num])
            _db.mass_action(sqls, logTransaction=False)

    _db.action('INSERT OR REPLACE INTO episode_refresh '
               '(tvdb_id, last_refreshed) '
               'VALUES (?,?)',
               [tvdb_id, time.time()])


def _get_show_last_refreshed(tvdb_id):
    """
    Get the timestamp of the last refresh for a show.

    @param tvdb_id: int
    @return: Returns a timestamp, or None if no refresh
    @rtype: int
    """
    if tvdb_id is None:
        return None

    db = _get_db()
    rows = db.select('SELECT last_refreshed '
                     'FROM episode_refresh '
                     'WHERE tvdb_id = ?', [tvdb_id])
    if rows:
        return int(rows[0]['last_refreshed'])
    else:
        return None
