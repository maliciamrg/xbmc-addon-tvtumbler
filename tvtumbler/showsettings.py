'''
This file is part of TvTumbler.

Use this module for talking to the show_settings table (rather than direct db calls)
where possible - allows for centralised caching etc.

Created on Sep 12, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
from . import db, logger


def _get_db():
    _db = db.Connection(row_type='dict')
    try:
        dummy = _get_db._init_done
    except:
        _db.action('CREATE TABLE if not exists show_settings ('
                   'tvdb_id INTEGER, '
                   'follow INTEGER, '
                   'wanted_quality INTEGER, '
                   'PRIMARY KEY (tvdb_id))')
        _get_db._init_done = True
    return _db

_show_settings_row_cache = {}


def get_show_settings_row(tvdb_id):
    global _show_settings_row_cache
    try:
        return _show_settings_row_cache[tvdb_id]
    except KeyError:
        pass
    db = _get_db()
    rows = db.select('SELECT * FROM show_settings where tvdb_id = ?', [str(tvdb_id)])
    if rows:
        _show_settings_row_cache[tvdb_id] = rows[0]
    else:
        _show_settings_row_cache[tvdb_id] = None
    return _show_settings_row_cache[tvdb_id]


def set_show_settings_row(tvdb_id, follow=None, wanted_quality=None):
    global _show_settings_row_cache
    row = get_show_settings_row(tvdb_id)
    exists = bool(row)
    if not exists:
        row = {'tvdb_id': str(tvdb_id),
               'follow': 0,
               'wanted_quality': 0}

    if follow is not None:
        row['follow'] = int(follow)
    if wanted_quality is not None:
        row['wanted_quality'] = int(wanted_quality)

    if exists:
        _get_db().action('UPDATE show_settings SET follow=?, wanted_quality=? '
                         'WHERE tvdb_id = ?',
                         [row['follow'], row['wanted_quality'], row['tvdb_id']])
    else:
        _get_db().action('INSERT INTO show_settings (tvdb_id, follow, wanted_quality) '
                         'VALUES (?, ?, ?)',
                         [row['tvdb_id'], row['follow'], row['wanted_quality']])

    _show_settings_row_cache[tvdb_id] = row
    return exists


def get_all_tvdb_ids(followed_only=False):
    sql = 'SELECT tvdb_id FROM show_settings'
    if followed_only:
        sql = sql + ' WHERE follow'
    return [r['tvdb_id'] for r in _get_db().select(sql)]


def purge_missing_shows():
    """
    Delete any settings for shows that are not in the xmbc library any longer, and are not
    followed (so we're not looking for new ones either)
    """
    _db = _get_db()

    from .tv import TvShow
    xbmc_tvdb_ids = [str(t.tvdb_id) for t in TvShow.get_xbmc_shows()]
    not_followed_tvdb_ids = [str(r['tvdb_id']) for r in _db.select('SELECT tvdb_id '
                                                                   'FROM show_settings '
                                                                   'WHERE NOT follow')]
    # anything that's not followed, and not in xbmc, we can delete
    for t in not_followed_tvdb_ids:
        if t not in xbmc_tvdb_ids:
            logger.debug('Deleting tvdb_id "%s" from settings' % (t,))
            if t in _show_settings_row_cache:
                del _show_settings_row_cache[t]
            _db.action('DELETE FROM show_settings WHERE tvdb_id = ?', [t])
