'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import os
import sys
import threading

import xbmc
import xbmcaddon
import xbmcgui


__addon__ = xbmcaddon.Addon()
__addonpath__ = __addon__.getAddonInfo('path').decode('utf-8')

libs = os.path.join(__addonpath__, 'resources', 'lib')
sys.path.append(libs)

from tvtumbler.gui.shows import TvTumblerShows

threading.current_thread().name = 'gui'

w = TvTumblerShows('script-tvtumbler-shows.xml', __addonpath__, "Default")
w.doModal()
del w
