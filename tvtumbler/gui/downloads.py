'''
This file is part of TvTumbler.

Created on Sep 21, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
from datetime import datetime, date
import os
import sys
import threading
import time

import xbmc
import xbmcaddon
import xbmcgui

from .. import quality, logger
from ..comms.client import service_api
from .actions import *


__addon__ = xbmcaddon.Addon()
__addonpath__ = __addon__.getAddonInfo('path').decode('utf-8')


class TvTumblerDownloads(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        self._running_downloads = dict()
        self._running_lock = threading.Lock()
        self._non_running_downloads = dict()
        self._non_running_lock = threading.Lock()

    def onInit(self):
        if not service_api.check_available(start_if_needed=False):
            dlg = xbmcgui.Dialog()
            dlg.ok('TvTumbler', 'Addon is either not running, or out of date.',
                   'Please restart XMBC.')
            return self.close()

        self._running_data_loader = threading.Thread(target=self._refresh_data, name='_refresh_data')
        self._running_data_loader._abort = False
        self._running_data_loader.start()

        self.getControl(120).selectItem(0)  # select the first row
        self.setFocus(self.getControl(120))

    def _refresh_data(self):
        num_previous_running = -1  # we keep track of this, so that when it changes, we know to query the non-running also
        full_refresh = False
        while not (self._running_data_loader._abort or xbmc.abortRequested):
            temp_running = service_api.get_running_downloads()
            # copy from temp_running into _running_downloads and then ...
            t_dict = {}
            for r in temp_running:
                t_dict[r['rowid']] = r
            with self._running_lock:
                self._running_downloads = t_dict

            if num_previous_running != len(self._running_downloads):
                non_running = service_api.get_non_running_downloads()
                logger.debug('got non_running: ' + repr(non_running))
                t_dict = {}
                for r in non_running:
                    t_dict[r['rowid']] = r
                with self._non_running_lock:
                    self._non_running_downloads = t_dict
                num_previous_running = len(self._running_downloads)
                full_refresh = True

            self.updateDisplay(full=full_refresh)
            xbmc.sleep(4800)  # effectively this will be every 5 secs
            full_refresh = False

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
        elif action == ACTION_SELECT_ITEM:
            if self.getFocusId() == 205:  # follow/ignore button
                # self.toggleFollow()
                pass
            elif self.getFocusId() == 120:  # select a line on the list itself
                # self.toggleFollow()
                pass
            elif self.getFocusId() == 200:
                # self.add_show()
                pass
            elif self.getFocusId() == 201:
                pass
                # self.addFromLibrary()
            elif self.getFocusId() == 202:
                # self.openSettings()
                pass
            else:
                pass
                # self.eplist()
        elif action == ACTION_PARENT_DIR:
            action = ACTION_PREVIOUS_MENU
        elif action == ACTION_MOUSE_LEFT_CLICK:
            if self.getFocusId() == 205:  # follow/ignore button
                # self.toggleFollow()
                pass
            elif self.getFocusId() == 120:  # click a line on the list itself
                # self.toggleFollow()
                pass
            elif self.getFocusId() == 200:
                # self.add_show()
                pass
            elif self.getFocusId() == 201:
                pass
                # self.addFromLibrary()
            elif self.getFocusId() == 202:
                # self.openSettings()
                pass

        if (action == ACTION_PREVIOUS_MENU and
            self._running_data_loader and
            self._running_data_loader.is_alive()):
                self._running_data_loader._abort = True

        xbmcgui.WindowXMLDialog.onAction(self, action)



    def doMenu(self):
        pass
#         item, show = self._get_selected_item_and_show()
#         options = []
#         if item:
#             if show['followed']:
#                 options.append(('Ignore', self.toggleFollow))
#                 options.append(('Select Quality', self.select_wanted_quality))
#             else:
#                 options.append(('Follow', self.toggleFollow))
#         else:
#             # we have no non-item menu items
#             pass
#
#         if options:
#             dlg = xbmcgui.Dialog()
#             selected = dlg.select('Options', [o[0] for o in options])
#             if selected >= 0:
#                 options[selected][1]()

    def updateDisplay(self, full=False):
        def sizeof_fmt(num, zero_as='0'):
            if num is None or num == 0:
                return zero_as
            for x in ['bytes', 'KB', 'MB', 'GB']:
                if num < 1024.0 and num > -1024.0:
                    return "%3.1f%s" % (num, x)
                num /= 1024.0
            return "%3.1f%s" % (num, 'TB')

        def startdate_fmt(ts):
            dt = datetime.fromtimestamp(int(ts))
            last_midnight = datetime.combine(date.today(), datetime.min.time())
            age_since_mn = last_midnight - dt
            if dt >= last_midnight:
                _fmt = '%H:%M'
            elif age_since_mn.days < 7:
                _fmt = '%a %H:%M'
            else:
                _fmt = '%x'  # Locale's appropriate date representation.
            return dt.strftime(_fmt)

        def timedelta_fmt(start_ts, end_ts):
            secs = int(end_ts - start_ts)
            if secs < 90:
                return '%d secs' % (secs,)
            elif secs < 5400:  # 1.5 hrs
                return '%d mins' % (secs // 60,)
            elif secs < 86400:  # 24 hours
                h, s = divmod(secs, 3600)
                return '%d h %d m' % (h, s // 60)
            else:
                return '%d hours' % (secs // 3600,)
            # start_dt = datetime.fromtimestamp(start_ts)
            # end_dt = datetime.fromtimestamp(end_ts)
            # delta = end_dt - start_dt
            # return str(delta)

        def _update_listitem(i, d, running):
            if running:
                # --
                # A RUNNING download
                # --
                i.setLabel(d['name'])
                # this is a little trick to force refresh of the row
                if i.getLabel2() == d['status_text']:
                    i.setLabel2(d['status_text'] + ' ')
                else:
                    i.setLabel2(d['status_text'])
                start_time = startdate_fmt(int(d['start_time']))
                i.setProperty('start_time', start_time)
                # i.setProperty('total_size', str(sizeof_fmt(d['total_size'])))
                i.setProperty('progress', '%s/%s' % (sizeof_fmt(d['downloaded_size']),
                                                     sizeof_fmt(d['total_size'], '?')))
                if float(d['total_size']) < 0.0001:
                    progress = '0.0'
                else:
                    progress = "%.2f" % (100.0 * float(d['downloaded_size']) / float(d['total_size']))
                # logger.debug('progress = ' + progress)
                i.setProperty('download_progress', progress)
                i.setProperty('source', str(d['source']))
                i.setProperty('rowid', str(d['rowid']))
                i.setProperty('key', str(d['key']))
                i.setInfo('video', {"Genre": 'Running'})  # this controls the color of the status
                i.setInfo('data', d)
            else:
                # --
                # A completed/failed download
                # --
                i.setLabel(d['name'])
                status = str(d['final_status']) + ' (' + timedelta_fmt(int(d['start_time']), int(d['finish_time'])) + ')'
                i.setLabel2(status)
                start_time = startdate_fmt(int(d['start_time']))
                i.setProperty('start_time', start_time)
                # i.setProperty('total_size', str(sizeof_fmt(d['total_size'])))
                i.setProperty('progress', sizeof_fmt(d['total_size'], ''))
                #progress = "%.2f" % (100.0 * float(d['downloaded_size']) / float(d['total_size']))
                #i.setProperty('download_progress', progress)
                i.setProperty('source', str(d['source']))
                i.setProperty('rowid', str(d['rowid']))
                i.setProperty('key', str(d['key']))
                i.setInfo('video', {"Genre": d['final_status']})  # this controls the color of the status
                i.setInfo('data', d)

        lctrl = self.getControl(120)
        if full:
            lctrl.reset()
        items_to_remove = []
        keys_to_add = self._running_downloads.keys() + self._non_running_downloads.keys()

        # The first thing we do is to go through what's currently in the list, and update it.
        # (this won't have any effect of course if the list is empty)
        for i in range(0, lctrl.size()):
            item = lctrl.getListItem(i)
            rowid = int(item.getProperty('rowid'))
            in_running = rowid in self._running_downloads
            in_non_running = rowid in self._non_running_downloads
            if not in_running and not in_non_running:
                items_to_remove.append(i)
            else:
                keys_to_add.remove(rowid)  # need to remove it now, still running
                _update_listitem(item,
                                 self._running_downloads[rowid] if in_running else self._non_running_downloads[rowid],
                                 in_running)

        # Then remove anything we no longer need (again, no effect if the list is empty)
        for i in items_to_remove:
            # from here: http://forum.xbmc.org/showthread.php?tid=158937
            # window_instance.removeControl(window_instance.getControl(ID))
            lctrl.removeItem(i)  # actually, this works.  at least in Gotham.

        keys_to_add.sort(reverse=True)
        for k in keys_to_add:
            if k in self._running_downloads:
                d = self._running_downloads[k]
                item = xbmcgui.ListItem(label=d['name'],
                                        label2=d['status_text'])
                # item.addContextMenuItems([('Label', 'Action'), ('Label2', 'Action2')])
                _update_listitem(item, d, True)
            else:
                d = self._non_running_downloads[k]
                item = xbmcgui.ListItem(label=str(d['name']),
                                        label2=str(d['final_status']))
                _update_listitem(item, d, False)

            lctrl.addItem(item)

        # lctrl.setEnabled(bool(self._running_downloads))
        # lctrl.setSortMethod(1) # SORT_METHOD_LABEL
