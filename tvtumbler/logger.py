'''
Created on Jun 21, 2013

@author: dermot@buckley.ie
'''

__all__ = ['debug', 'info', 'notice', 'warning', 'severe', 'error', 'fatal',
           'log']

import threading
import xbmc
import sys

__addon__ = sys.modules["__main__"].__addon__
__addonname__ = __addon__.getAddonInfo('name')


def log(msg, level=xbmc.LOGDEBUG):
    '''
    Send a message to the xbmc log.

    @param msg: (string)
    @param level: (int)
    '''
    if type(msg).__name__ == 'unicode':
        msg = msg.encode('utf-8')

    threadName = threading.currentThread().getName()

    xbmc.log("[%s:%s] %s" % (__addonname__, threadName, msg.__str__()), level)


def debug(msg):
    """
    In depth information about the status of XBMC. This information can pretty
    much only be deciphered by a developer or long time XBMC power user.
    """
    log(msg, level=xbmc.LOGDEBUG)


def info(msg):
    """
    Something has happened. It's not a problem, we just thought you might want
    to know. Fairly excessive output that most people won't care about.
    """
    log(msg, level=xbmc.LOGINFO)


def notice(msg):
    """
    Similar to INFO but the average Joe might want to know about these events.
    This level and above are logged by default.
    """
    log(msg, level=xbmc.LOGNOTICE)


def warning(msg):
    """
    Something potentially bad has happened. If XBMC did something you didn't
    expect, this is probably why. Watch for errors to follow.
    """
    log(msg, level=xbmc.LOGWARNING)


def error(msg):
    """
    This event is bad. Something has failed. You likely noticed problems with
    the application be it skin artifacts, failure of playback a crash, etc.
    """
    log(msg, level=xbmc.LOGERROR)


def severe(msg):
    log(msg, level=xbmc.LOGSEVERE)


def fatal(msg):
    log(msg, level=xbmc.LOGFATAL)

# LOGDEBUG = 0
# LOGINFO = 1
# LOGNOTICE = 2
# LOGWARNING = 3
# LOGERROR = 4
# LOGSEVERE = 5
# LOGFATAL = 6
# LOGNONE = 7
