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


def _get_db(row_type=None):
    _db = db.Connection(row_type=row_type)
    try:
        dummy = _get_db._init_done
    except:
        _db.action('CREATE TABLE if not exists dl_log ('
                              'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                              'key VARCHAR(255), '
                              'tvdb_id INTEGER, '
                              'tvshowid INTEGER, '
                              'name TEXT, '
                              'source VARCHAR(255), '
                              'started_at INTEGER, '  # timestamp
                              'finished_at INTEGER, '  # timestamp
                              'final_status VARCHAR(255), '
                              'total_size INTEGER, '
                              'quality INTEGER)')
#         _db.action('CREATE TABLE if not exists xem_refresh ('
#                               'tvdb_id INTEGER PRIMARY KEY, '
#                               'last_refreshed INTEGER)')
        _get_db._init_done = True
    return _db


def get_non_running_downloads(properties=['rowid', 'key', 'name', 'final_status', 'total_size',
                                          'start_time', 'finish_time', 'source', 'quality'], limit=30):
    conn = _get_db(row_type='dict')
    result = []
    for r in conn.select('SELECT * FROM dl_log '
                         'WHERE finished_at IS NOT NULL '
                         'ORDER BY started_at DESC LIMIT ?', [limit]):
        d = dict()
        for k in properties:
            # these ones are properties (we can read them straight)
            if k in ['key', 'name', 'final_status', 'total_size', 'source', 'quality']:
                d[k] = r.get(k, None)
            elif k == 'rowid':
                d[k] = r['id']
            elif k == 'start_time':
                d[k] = r['started_at']
            elif k == 'finish_time':
                d[k] = r['finished_at']
            else:
                logger.notice('Attempt to get unknown property ' + k)
        result.append(d)
    logger.debug('non running downloads (from db): ' + repr(result))
    return result


def log_download_start(download):
    '''
    @type download: tvtumbler.downloaders.base.Download
    '''
    conn = _get_db()
    dlable = download.downloadable
    show = dlable.tvshow
    feeder = dlable.feeder
    result = conn.action('INSERT INTO dl_log (key, tvdb_id, tvshowid, name, source, started_at, quality) VALUES (?,?,?,?,?,?,?)',
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
        result = conn.select('SELECT max(ROWID) FROM dl_log WHERE key = ? AND finished_at IS NULL',
                            [download.key])
        if result:
            rowid = result[0][0]
        else:
            raise Exception('Unable to find a matching start record for this download!')

    conn.action('UPDATE dl_log SET finished_at = ?, final_status = ?, total_size = ? WHERE ROWID = ?',
                [time.time(), 'Failed', download.total_size, rowid])



def log_download_finish(download):
    conn = _get_db()
    try:
        rowid = download.rowid
    except (KeyError, AttributeError):
        result = conn.select('SELECT max(ROWID) FROM dl_log WHERE key = ? AND finished_at IS NULL',
                            [download.key])
        if result:
            rowid = result[0][0]
        else:
            raise Exception('Unable to find a matching start record for this download!')

    conn.action('UPDATE dl_log SET finished_at = ?, final_status = ?, total_size = ? WHERE ROWID = ?',
                [time.time(), 'Downloaded', download.total_size, rowid])
