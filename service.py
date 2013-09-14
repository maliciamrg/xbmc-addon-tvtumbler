#!/usr/bin/python
'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import sys
import os
import xbmc
import xbmcaddon

__addon__ = xbmcaddon.Addon()
__addonversion__ = __addon__.getAddonInfo('version')
__addonname__ = __addon__.getAddonInfo('name')
__addonpath__ = __addon__.getAddonInfo('path').decode('utf-8')
# __icon__ = __addon__.getAddonInfo('icon')
# __localize__ = __addon__.getLocalizedString

libs = os.path.join(__addonpath__, 'resources', 'lib')
sys.path.append(libs)

import tvtumbler
import tvtumbler.logger as logger


if __name__ == '__main__':
    logger.notice('%s version %s' % (__addonname__, __addonversion__))
    logger.notice('Python version %s' % sys.version)

    tvtumbler.start()

    while (not xbmc.abortRequested):
        xbmc.sleep(1000)

    tvtumbler.halt()
