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

if len(sys.argv) > 1:
    # if there are any params, then we are running in non-interactive mode
    print "argv: " + repr(sys.argv)
else:
    from tvtumbler.gui.main import TvTumblerMain

    threading.current_thread().name = 'gui'

    w = TvTumblerMain('script-tvtumbler-main.xml', __addonpath__, "Default")
    w.doModal()
    del w

