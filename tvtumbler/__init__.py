'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

from __future__ import with_statement
from threading import Lock
from .schedule import SchedulerThread
from . import feeder
# from . import downloader
from . import logger

feederThread = None
# downloaderThread = None
started = False
start_stop_lock = Lock()

FEEDER_RUN_INTERVAL_SECS = 15 * 60
# DOWNLOADER_RUN_INTERVAL_SECS = 5


def start():
    '''
    Startup
    '''
    global feederThread, FEEDER_RUN_INTERVAL_SECS
    # global downloaderThread, DOWNLOADER_RUN_INTERVAL_SECS
    global started, start_stop_lock

    logger.info(u'Starting')

    with start_stop_lock:
        if started:
            logger.warning('Attempt to start when already started.')
            return

        feederThread = SchedulerThread(action=feeder.run,
                                    threadName="FEEDER",
                                    runIntervalSecs=FEEDER_RUN_INTERVAL_SECS)
        feederThread.start(20)

#         downloaderThread = SchedulerThread(action=downloader.run,
#                                 threadName='DOWNLOADER',
#                                 runIntervalSecs=DOWNLOADER_RUN_INTERVAL_SECS)
#         downloaderThread.start(30)

        started = True
        logger.info(u'Started')


def halt():
    '''
    Shutdown
    '''
    global feederThread, downloaderThread
    global started, start_stop_lock

    logger.info(u'Stopping')

    with start_stop_lock:
        if not started:
            logger.warning('Attempt to stop when not started.')
            return

        logger.debug(u'setting abort on threads')
        feederThread.abort = True
#         downloaderThread.abort = True

#         time.sleep(4)
#
#         if feederThread.is_alive():
#             logger.warning(u'The threads failed to stop within 4 secs')

        started = False
        logger.info(u'Stopped')
