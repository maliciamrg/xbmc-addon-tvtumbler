'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

from __future__ import with_statement

import os.path
import threading
import time
import xbmc
import sys
import xbmcvfs

from . import logger


try:
    from sqlite3 import dbapi2 as sqlite
    logger.info("Loading sqlite3 as DB engine")
except:
    from pysqlite2 import dbapi2 as sqlite
    logger.info("Loading pysqlite2 as DB engine")


__addon__ = sys.modules[ "__main__" ].__addon__
# __addonpath__ = __addon__.getAddonInfo('path').decode('utf-8')

db_lock = threading.Lock()


def db_path(filename="tvtumbler.db"):
    """
    Get the correct database path for filename.

    This will create the needed directory structure if not already present.

    @param filename: (str) The sqlite database filename to use
    @return: (str) the correct location of the database file.
    """
    path = xbmc.translatePath(
                    __addon__.getAddonInfo('profile').decode('utf-8'))
    if not xbmcvfs.exists(path):
        logger.notice(u'Creating path: %s' % path)
        xbmcvfs.mkdir(path)
    return os.path.join(path, filename)


class Connection(object):
    def __init__(self, filename="tvtumbler.db", row_type=None):

        self.filename = filename
        self.connection = sqlite.connect(db_path(filename), 20)
        if row_type == "dict":
            self.connection.row_factory = self._dict_factory
        else:
            self.connection.row_factory = sqlite.Row

    def mass_action(self, querylist, logTransaction=False):

        with db_lock:

            if querylist == None:
                return

            sqlResult = []
            attempt = 0

            while attempt < 5:
                try:
                    for qu in querylist:
                        if len(qu) == 1:
                            if logTransaction:
                                logger.debug(qu[0])
                            sqlResult.append(self.connection.execute(qu[0]))
                        elif len(qu) > 1:
                            if logTransaction:
                                logger.debug(qu[0] + " with args " +
                                             str(qu[1]))
                            sqlResult.append(self.connection.execute(qu[0],
                                                                     qu[1]))
                    self.connection.commit()
                    logger.debug(u"Transaction with " + str(len(querylist)) +
                                 u" querys executed")
                    return sqlResult
                except sqlite.OperationalError, e:
                    sqlResult = []
                    if self.connection:
                        self.connection.rollback()
                    if ("unable to open database file" in e.message or
                        "database is locked" in e.message):
                        logger.warning(u"DB error: %s" % e)
                        attempt += 1
                        xbmc.sleep(1000)
                    else:
                        logger.error(u"DB error: %s" % e)
                        raise
                except sqlite.DatabaseError, e:
                    sqlResult = []
                    if self.connection:
                        self.connection.rollback()
                    logger.error(u"Fatal error executing query: %s" % e)
                    raise

            return sqlResult

    def action(self, query, args=None):

        with db_lock:

            if query == None:
                return

            sqlResult = None
            attempt = 0

            while attempt < 5:
                try:
                    if args == None:
                        logger.debug(self.filename + ": " + query)
                        sqlResult = self.connection.execute(query)
                    else:
                        logger.debug(self.filename + ": " + query +
                                     " with args " + str(args))
                        sqlResult = self.connection.execute(query, args)
                    self.connection.commit()
                    # get out of the loop since we were successful
                    break
                except sqlite.OperationalError, e:
                    if ("unable to open database file" in str(e) or
                        "database is locked" in str(e)):
                        logger.warning(u"DB error: %s" % e)
                        attempt += 1
                        xbmc.sleep(1000)
                    else:
                        logger.error(u"DB error: %s" % e)
                        raise
                except sqlite.DatabaseError, e:
                    logger.error(u"Fatal error executing query: %s" % e)
                    raise

            return sqlResult

    def select(self, query, args=None):

        sqlResults = self.action(query, args).fetchall()

        if sqlResults == None:
            return []

        return sqlResults

    # http://stackoverflow.com/questions/3300464/how-can-i-get-dict-from-sqlite-query
    def _dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
