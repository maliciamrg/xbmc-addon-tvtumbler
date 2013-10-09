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

        self._update_loading_dialog(40, 'Checking downloaders ...')

        if (__addon__.getSetting('trpc_enable') != 'true' and
            __addon__.getSetting('libtorrent_enable') != 'true'):
            self._hide_loading_dialog()
            dlg = xbmcgui.Dialog()
            if dlg.yesno(heading='TvTumbler', line1='No Downloader enabled.',
                         line2='Would you like to view the addon settings?',
                         nolabel='No', yeslabel='Yes'):
                __addon__.openSettings()

        self._update_loading_dialog(60, 'Checking feeders ...')

        if (__addon__.getSetting('ezrss_enable') != 'true' and
            __addon__.getSetting('showrss_enable') != 'true' and
            __addon__.getSetting('publichd_enable') != 'true'):
            self._hide_loading_dialog()
            dlg = xbmcgui.Dialog()
            if dlg.yesno(heading='TvTumbler', line1='No Feeders enabled.',
                         line2='Would you like to view the addon settings?',
                         nolabel='No', yeslabel='Yes'):
                __addon__.openSettings()

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
