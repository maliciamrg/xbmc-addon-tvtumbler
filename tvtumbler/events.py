'''
This file is part of TvTumbler.

Created on Sep 6, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import traceback
import xbmc

from . import logger


ABORT_REQUESTED = 'abortRequested'
VIDEO_LIBRARY_UPDATED = 'videoLibraryUpdated'
SCREENSAVED_ACTIVATED = 'screensaverActivated'
SCREENSAVER_DEACTIVATED = 'screensaverDeactivated'
SETTINGS_CHANGED = 'settingsChanged'
EXCEPTIONS_CHANGED = 'exceptionsChanged'

_listeners = {
    ABORT_REQUESTED: set(),
    VIDEO_LIBRARY_UPDATED: set(),
    SCREENSAVED_ACTIVATED: set(),
    SCREENSAVER_DEACTIVATED: set(),
    SETTINGS_CHANGED: set(),
    EXCEPTIONS_CHANGED: set(),
}


def add_event_listener(eventName, listener):
    global _listeners
    _listeners[eventName].add(listener)


def _call_listeners(eventName):
    global _listeners
    for fn in _listeners[eventName]:
        try:
            fn()
        except Exception, e:
            logger.error('Exception when calling listener: ' + str(e))
            logger.debug(traceback.format_exc())


class ParentMonitor(xbmc.Monitor):
    def onAbortRequested(self):
        logger.debug("ParentMonitor: onAbortRequested()")
        _call_listeners(ABORT_REQUESTED)

    def onDatabaseUpdated(self, database):
        logger.debug("ParentMonitor: onDatabaseUpdated()")
        if database == 'video':
            _call_listeners(VIDEO_LIBRARY_UPDATED)

    def onScreensaverActivated(self):
        logger.debug("ParentMonitor: onScreensaverActivated()")
        _call_listeners(SCREENSAVED_ACTIVATED)

    def onScreensaverDeactivated(self):
        logger.debug("ParentMonitor: onScreensaverDeactivated()")
        _call_listeners(SCREENSAVER_DEACTIVATED)

    def onSettingsChanged(self):
        logger.debug("ParentMonitor: onSettingsChanged()")
        _call_listeners(SETTINGS_CHANGED)

    @staticmethod
    def onExceptionsChanged():
        logger.debug("ParentMonitor: onExceptionsChanged()")
        _call_listeners(EXCEPTIONS_CHANGED)

m = ParentMonitor()
