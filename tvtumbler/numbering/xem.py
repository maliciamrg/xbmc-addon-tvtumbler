'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import time
from .. import db, logger, utils
import xbmc

MAX_XEM_AGE_SECS = 86400  # 1 day


def _get_db():
    _db = db.Connection()
    try:
        dummy = _get_db._init_done
    except:
        _db.action('CREATE TABLE if not exists xem_num ('
                              'tvdb_id INTEGER, '
                              'tvdb_season INTEGER, '
                              'tvdb_episode INTEGER, '
                              'scene_season INTEGER, '
                              'scene_episode INTEGER, '
                      'PRIMARY KEY (tvdb_id, tvdb_season, tvdb_episode, '
                                   'scene_season, scene_episode))')
        _db.action('CREATE TABLE if not exists xem_refresh ('
                              'tvdb_id INTEGER PRIMARY KEY, '
                              'last_refreshed INTEGER)')
        _get_db._init_done = True
    return _db


def get_scene_numbering_from_xem(tvdb_id, tvdbSeason, tvdbEpisode):
    """
    Returns the scene numbering, as retrieved from xem.
    Refreshes/Loads as needed.

    @param tvdb_id: (int)
    @param tvdbSeason: (int)
    @param tvdbEpisode: (int)
    @return: A list of tuples (scene_season, scene_episode).  The list
             will be empty if there is no special xem mapping.
    """
    if tvdb_id is None or tvdbSeason is None or tvdbEpisode is None:
        return []

    if _xem_refresh_needed(tvdb_id) and not xbmc.abortRequested:
        _xem_refresh(tvdb_id)

    db = _get_db()
    rows = db.select('SELECT scene_season, scene_episode '
                        'FROM xem_num '
                        'WHERE tvdb_id = ? '
                        'AND tvdb_season = ? AND tvdb_episode = ? '
                        'ORDER BY scene_season ASC, scene_episode ASC',
                        [tvdb_id, tvdbSeason, tvdbEpisode])
    if rows:
        return [(int(r["scene_season"]), int(r["scene_episode"]))
                for r in rows]
    else:
        return []


def get_tvdb_numbering_from_xem(tvdb_id, sceneSeason, sceneEpisode):
    """
    Reverse of get_scene_numbering_from_xem: lookup the tvdb season
    and episodes using scene numbering.

    @param tvdb_id: int
    @param sceneSeason: int
    @param sceneEpisode: int
    @return: A list of tuples of (tvdb_season, tvdb_episode) - both ints.
             Returns an empty list if there is no xem mapping.
    """
    if tvdb_id is None or sceneSeason is None or sceneEpisode is None:
        return []

    if _xem_refresh_needed(tvdb_id) and not xbmc.abortRequested:
        _xem_refresh(tvdb_id)

    db = _get_db()
    rows = db.select('SELECT tvdb_season, tvdb_episode '
                     'FROM xem_num '
                     'WHERE tvdb_id = ? '
                     'AND scene_season = ? '
                     'AND scene_episode = ? '
                     'ORDER BY tvdb_season ASC, tvdb_episode ASC',
                     [tvdb_id, sceneSeason, sceneEpisode])
    if rows:
        return [(int(r["tvdb_season"]), int(r["tvdb_season"]))
                for r in rows]
    else:
        return []


def _xem_refresh_needed(tvdb_id):
    """
    Is a refresh needed on a show?

    @param tvdb_id: int
    @return: bool
    """
    if tvdb_id is None:
        return False

    db = _get_db()
    rows = db.select('SELECT last_refreshed '
                     'FROM xem_refresh '
                     'WHERE tvdb_id = ?', [tvdb_id])
    if rows:
        return time.time() > (int(rows[0]['last_refreshed']) +
                              MAX_XEM_AGE_SECS)
    else:
        return True


def _xem_refresh(tvdb_id):
    """
    Refresh data from xem for a tv show

    @param tvdb_id: int
    """
    if tvdb_id is None:
        return

    urls = ['http://thexem.de/map/all?id=%s&origin=tvdb&destination=scene',
            'http://show-api.tvtumbler.com/api/thexem/all?id=%s&origin=tvdb&destination=scene']

    try:
        tvdb_id = str(tvdb_id)

        logger.debug(u'Looking up xem mapping for %s' % (tvdb_id,))
        result = None
        for url in urls:
            result = utils.get_url_as_json(url % (tvdb_id,))
            if result:
                break  # stop at first success

        if result:
            db = _get_db()
            db.action('INSERT OR REPLACE INTO xem_refresh '
                      '(tvdb_id, last_refreshed) '
                      'VALUES (?,?)',
                      [tvdb_id, time.time()])
            if result['result'] == 'success':
                db.action("DELETE FROM xem_num where tvdb_id = ?", [tvdb_id])
                for entry in result['data']:
                    # 'scene' is always present, scene_2 is for doubles, etc.
                    for keyname in ('scene', 'scene_2', 'scene_3', 'scene_4'):
                        if keyname in entry:
                            db.action('INSERT OR REPLACE INTO xem_num ('
                                  'tvdb_id, '
                                  'tvdb_season, '
                                  'tvdb_episode, '
                                  'scene_season, '
                                  'scene_episode) '
                                  'VALUES (?,?,?,?,?)',
                                  [tvdb_id,
                                   entry['tvdb']['season'],
                                   entry['tvdb']['episode'],
                                   entry[keyname]['season'],
                                   entry[keyname]['episode']])
            else:
                logger.debug(u'No thexem.de for show %s with message "%s"'
                             % (tvdb_id, result['message']))
        else:
            logger.info(u"Empty lookup result - no data from thexem.de for %s"
                        % (tvdb_id,))
    except Exception, e:
        logger.warning(u"Exception while refreshing thexem data for " +
                       str(tvdb_id) + ": " + str(e))


# def get_all_xem_mappings_for_show(tvdb_id):
#     """
#     Returns a dict of (tvdbSeason, tvdbEpisode) : (sceneSeason, sceneEpisode)
#     mappings for an entire show.  Both the keys and values of the dict are
#     tuples. Will be empty if there are no scene numbers set in xem
#     """
#     if tvdb_id is None:
#         return {}
#
#     if _xem_refresh_needed(tvdb_id) and not xbmc.abortRequested:
#         _xem_refresh(tvdb_id)
#
#     db = _get_db()
#     rows = db.select('''SELECT tvdb_season, tvdb_episode,
#                         scene_season, scene_episode
#                         FROM xem_num WHERE tvdb_id = ?
#                         ORDER BY tvdb_season ASC, tvdb_episode ASC''',
#                         [tvdb_id])
#     result = {}
#     for row in rows:
#         result[(int(row['season']), int(row['episode']))] =
#            (int(row['scene_season']), int(row['scene_episode']))
#
#     return result
