#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2013 Dermot Buckley
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys
import os
import time
import xbmc
import xbmcaddon

__addon__           = xbmcaddon.Addon()
__addonversion__    = __addon__.getAddonInfo('version')
__addonname__       = __addon__.getAddonInfo('name')
__addonpath__       = __addon__.getAddonInfo('path').decode('utf-8')
# __icon__         = __addon__.getAddonInfo('icon')
# __localize__    = __addon__.getLocalizedString

import tvtumbler
import tvtumbler.logger as logger


if __name__ == '__main__':
    logger.notice('%s version %s' % (__addonname__, __addonversion__))
    logger.notice('Python version %s' % sys.version)

    libs = os.path.join(__addonpath__, 'resources/lib')
    sys.path.append(libs)

    tvtumbler.start()

    while (not xbmc.abortRequested):
        time.sleep(1)

    tvtumbler.halt()
