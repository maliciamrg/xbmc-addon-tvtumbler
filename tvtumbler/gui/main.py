'''
This file is part of TvTumbler.

Created on Sep 21, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from .. import logger
# from ..comms.client import service_api
from .actions import *
from .common import TvTumblerWindowXMLDialog
from .contextmenu import ContextMenuDialog


__addon__ = xbmcaddon.Addon()
__addonpath__ = __addon__.getAddonInfo('path').decode('utf-8')


class TvTumblerMain(TvTumblerWindowXMLDialog):
    def __init__(self, *args, **kwargs):
        pass

    def onInit(self):
        self._show_loading_dialog()
        if not self.check_service_ok():
            self._hide_loading_dialog()
            self.close()
            return

#         self.getControl(120).selectItem(0)  # select the first row
#         self.setFocus(self.getControl(120))
        self._hide_loading_dialog()

    def onClick(self, controlId):
        pass

    def onFocus(self, controlId):
        logger.debug('onFocus(' + str(controlId) + ')')
        self.controlId = controlId

    def onAction(self, action):
        logger.debug("ACTION: " + str(action.getId()) + " FOCUS: " +
                     str(self.getFocusId()) + " BC: " + str(action.getButtonCode()))
        if action == ACTION_CONTEXT_MENU:
            self.doMenu()
        elif action in (ACTION_SELECT_ITEM, ACTION_MOUSE_LEFT_CLICK):
            if self.getFocusId() == 200:  # Shows
                self.open_shows()
            elif self.getFocusId() == 201:  # Calendar
                self.open_calender()
            elif self.getFocusId() == 202:  # Downloads
                self.open_downloads()
            elif self.getFocusId() == 203:  # status
                self.open_status()
            else:
                pass
        elif action == ACTION_PARENT_DIR:
            action = ACTION_PREVIOUS_MENU

        xbmcgui.WindowXMLDialog.onAction(self, action)

    def open_settings(self):
        __addon__.openSettings()
        # self.loadSettings()

    def open_downloads(self):
        from .downloads import TvTumblerDownloads
        w = TvTumblerDownloads('script-tvtumbler-downloads.xml', __addonpath__, "Default")
        w.doModal()
        del w

    def open_shows(self):
        from .shows import TvTumblerShows
        w = TvTumblerShows('script-tvtumbler-shows.xml', __addonpath__, "Default")
        w.doModal()
        del w

    def open_calender(self):
        from .calendar import TvTumblerCalendar
        w = TvTumblerCalendar('script-tvtumbler-calendar.xml', __addonpath__, "Default")
        w.doModal()
        del w

    def open_status(self):
        pass

    def doMenu(self):
        pass
