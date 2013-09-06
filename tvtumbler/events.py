'''
This file is part of TvTumbler.

Created on Sep 6, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import xbmc
from . import logger


class ParentMonitor(xbmc.Monitor):
    def onAbortRequested(self):
        logger.debug("ParentMonitor: onAbortRequested()")

    def onDatabaseUpdated(self, database):
        logger.debug("ParentMonitor: onDatabaseUpdated()")

    def onScreensaverActivated(self):
        logger.debug("ParentMonitor: onScreensaverActivated()")

    def onScreensaverDeactivated(self):
        logger.debug("ParentMonitor: onScreensaverDeactivated()")

m = ParentMonitor()
