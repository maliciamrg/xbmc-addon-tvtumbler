'''
This file is part of TvTumbler.

Created on Sep 21, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import datetime
import traceback

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from .. import logger
from ..comms.client import service_api
from .actions import *
from .common import TvTumblerWindowXMLDialog
from .contextmenu import ContextMenuDialog


__addon__ = xbmcaddon.Addon()
__addonpath__ = __addon__.getAddonInfo('path').decode('utf-8')


class TvTumblerCalendar(TvTumblerWindowXMLDialog):
    def __init__(self, *args, **kwargs):
        pass

    def onInit(self):
        try:
            self._show_loading_dialog()
            if not self.check_service_ok():
                self._hide_loading_dialog()
                self.close()
                return

            yesterday = datetime.date.today() - datetime.timedelta(days=1)

            for i in range(7):
                self._update_loading_dialog(25 + 10 * i, 'Loading Schedule ...')
                thedate = yesterday + datetime.timedelta(days=i)
                if self._loading_dialog.iscanceled():
                    self._hide_loading_dialog()
                    self.close()
                    return
                self.populate_for_date(i, thedate)

#             self.populate_for_date(0, '2013-09-28')
#             self.populate_for_date(1, '2013-09-29')
#             self.populate_for_date(2, '2013-09-30')
#             self.populate_for_date(3, '2013-10-01')
#             self.populate_for_date(4, '2013-10-02')
#             self.populate_for_date(5, '2013-10-03')
#             self.populate_for_date(6, '2013-10-04')

    #         self.getControl(120).selectItem(0)  # select the first row
    #         self.setFocus(self.getControl(120))
        except Exception, e:
            logger.error(e)
            logger.error(traceback.format_exc)
        self._hide_loading_dialog()

    def populate_for_date(self, day_index, airdate):
        if __addon__.getSetting('cal_enable_images') == 'true':
            properties = ['episodeid', 'tvdb_season', 'tvdb_episode', 'title',
                        'art', 'show_fanart', 'show_thumbnail', 'show_tvdb_id',
                        'show_name', 'have_state']
        else:
            properties = ['episodeid', 'tvdb_season', 'tvdb_episode', 'title',
                         'show_tvdb_id', 'show_name', 'have_state']

        eps = service_api.get_episodes_on_date(firstaired=airdate, properties=properties)
        logger.debug('for ' + str(airdate) + ' got: ' + repr(eps))

        dayLabel = self.getControl(130 + day_index)
        monLabel = self.getControl(140 + day_index)
        dtLabel = self.getControl(150 + day_index)

        dayLabel.setLabel(airdate.strftime('%a'))
        monLabel.setLabel(airdate.strftime('%b'))
        dtLabel.setLabel(airdate.strftime('%d'))

        lctrl = self.getControl(120 + day_index)
        lctrl.reset()
        for ep in eps:
#             {u'tvshow.fanart': u'image://http%3a%2f%2fthetvdb.com%2fbanners%2ffanart%2foriginal%2f248596-1.jpg/',
#              u'tvshow.poster': u'image://http%3a%2f%2fthetvdb.com%2fbanners%2fposters%2f248596-3.jpg/',
#              u'thumb': u'image://http%3a%2f%2fthetvdb.com%2fbanners%2fepisodes%2f248596%2f4096825.jpg/',
#              u'tvshow.banner': u'image://http%3a%2f%2fthetvdb.com%2fbanners%2fgraphical%2f248596-g2.jpg/'}


            image_path = ''
            if 'art' in ep and ep['art']:
                for k in [u'thumb', u'tvshow.fanart']:
                    if k in ep['art'] and ep['art'][k]:
                        image_path = ep['art'][k]
                        break
            if image_path == '':
                for k in ['show_thumbnail', 'show_fanart']:
                    if k in ep and ep[k]:
                        image_path = ep[k]
                        break

            item = xbmcgui.ListItem(label=ep['title'],
                                    label2='%dx%d' % (ep['tvdb_season'], ep['tvdb_episode']),
                                    iconImage=image_path)
            item.setProperty('show_name', ep['show_name'])
            # item.setProperty('Genre', ep['have_state'] if 'have_state' in ep and ep['have_state'] else '')
            item.setInfo('video', {"Genre": ep['have_state'] if 'have_state' in ep and ep['have_state'] else ''})
            # item.setIconImage(ep['show_fanart'])

            lctrl.addItem(item)

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



    def open_status(self):
        pass

    def doMenu(self):
        pass
