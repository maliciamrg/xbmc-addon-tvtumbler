'''
This file is part of TvTumbler.

Created on Sep 20, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import time
from . import logger, db


def _get_db():
    _db = db.Connection()
    try:
        dummy = _get_db._init_done
    except:
        _db.action('CREATE TABLE if not exists dllog ('
                              'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                              'key VARCHAR(255), '
                              'tvdb_id INTEGER, '
                              'tvshowid INTEGER, '
                              'name TEXT, '
                              'source VARCHAR(255), '
                              'started_at INTEGER, '  # timestamp
                              'finished_at INTEGER, '  # timestamp
                              'final_status VARCHAR(255), '
                              'quality INTEGER)')
#         _db.action('CREATE TABLE if not exists xem_refresh ('
#                               'tvdb_id INTEGER PRIMARY KEY, '
#                               'last_refreshed INTEGER)')
        _get_db._init_done = True
    return _db


def log_download_start(download):
    '''
    @type download: tvtumbler.downloaders.base.Download
    '''
    conn = _get_db()
    dlable = download.downloadable
    show = dlable.tvshow
    feeder = dlable.feeder
    result = conn.action('INSERT INTO dllog (key, tvdb_id, tvshowid, name, source, started_at, quality) VALUES (?,?,?,?,?,?,?)',
                         [download.key,  # key
                          show.tvdb_id,  # tvdb_id
                          show.tvshowid,  # tvshowid (xbmc id)
                          dlable.name,  # name
                          feeder.get_name(),  # source
                          time.time(),  # started_at,
                          dlable.quality])  # quality
    # logger.debug('result from insert: ' + repr(result))
    result = conn.select('select last_insert_rowid()')
    # logger.debug('result from last_insert_rowid: ' + repr(result))
    download.rowid = result[0][0]
    return result[0][0]


def log_download_fail(download):
    conn = _get_db()
    try:
        rowid = download.rowid
    except (KeyError, AttributeError):
        result = conn.select('SELECT max(ROWID) FROM dllog WHERE key = ? AND finished_at IS NULL',
                            [download.key])
        if result:
            rowid = result[0][0]
        else:
            raise Exception('Unable to find a matching start record for this download!')

    conn.action('UPDATE dllog SET finished_at = ?, final_status = ? WHERE ROWID = ?',
                [time.time(), 'Failed', rowid])


def log_download_finish(download):
    conn = _get_db()
    try:
        rowid = download.rowid
    except (KeyError, AttributeError):
        result = conn.select('SELECT max(ROWID) FROM dllog WHERE key = ? AND finished_at IS NULL',
                            [download.key])
        if result:
            rowid = result[0][0]
        else:
            raise Exception('Unable to find a matching start record for this download!')

    conn.action('UPDATE dllog SET finished_at = ?, final_status = ? WHERE ROWID = ?',
                [time.time(), 'Downloaded', rowid])
