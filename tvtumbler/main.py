'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

from __future__ import with_statement

from threading import Lock

from . import events, feeder, logger, housekeeper, backlogger
from .schedule import SchedulerThread
from .comms import server


feederThread = None
housekeeperThread = None
backloggerThread = None
started = False
start_stop_lock = Lock()
shutdownRequested = False

FEEDER_RUN_INTERVAL_SECS = 3 * 60
HOUSEKEEPER_RUN_INTERVAL_SECS = 5000
BACKLOGGER_RUN_INTERVAL_SECS = 60 * 60 * 16


def start():
    '''
    Startup
    '''
    global feederThread, FEEDER_RUN_INTERVAL_SECS
    global housekeeperThread, HOUSEKEEPER_RUN_INTERVAL_SECS
    global backloggerThread, BACKLOGGER_RUN_INTERVAL_SECS
    global started, start_stop_lock

    logger.info(u'Starting')

    with start_stop_lock:
        if started:
            logger.warning('Attempt to start when already started.')
            return

        server.run_server()

        feederThread = SchedulerThread(action=feeder.run,
                                    threadName="FEEDER",
                                    runIntervalSecs=FEEDER_RUN_INTERVAL_SECS)
        feederThread.start(20)

        housekeeperThread = SchedulerThread(action=housekeeper.run,
                                threadName='HOUSEKEEPER',
                                runIntervalSecs=HOUSEKEEPER_RUN_INTERVAL_SECS)
        housekeeperThread.start(1000)

        backloggerThread = SchedulerThread(action=backlogger.run,
                                threadName='BACKLOGGER',
                                runIntervalSecs=BACKLOGGER_RUN_INTERVAL_SECS)
        backloggerThread.start(600)

        started = True
        logger.info(u'Started')


def halt():
    '''
    Shutdown
    '''
    global feederThread, housekeeperThread, backloggerThread
    global started, start_stop_lock

    logger.info(u'Stopping')

    with start_stop_lock:
        if not started:
            logger.warning('Attempt to stop when not started.')
            return

        logger.debug(u'setting abort on threads')
        feederThread.abort = True
        housekeeperThread.abort = True
        backloggerThread.abort = True

#         time.sleep(4)
#
#         if feederThread.is_alive():
#             logger.warning(u'The threads failed to stop within 4 secs')

        started = False
        logger.info(u'Stopped')
