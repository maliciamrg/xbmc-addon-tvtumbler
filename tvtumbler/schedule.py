'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''


import time
import threading
import traceback

from . import logger


class SchedulerThread(threading.Thread):

    """
    Base class for all scheduler threads.

    To use, inherit from this class, and override runAction(), or use this
    class, passing a function to 'action' in the xtor.
    """

    def __init__(self, action=None, threadName="Scheduler", 
                 runIntervalSecs=10 * 60):
        '''
        Xtor.  Creates a new thread.

        Don't forget to call start() to start it.

        @param threadName: (string) Name used for the thread (mostly for
            debugging)
        @param runIntervalSecs: (int) Interval in seconds between calls to
            runAction().
        '''
        threading.Thread.__init__(self, name=threadName)
        self.daemon = True
        self.threadName = threadName
        self.runIntervalSecs = runIntervalSecs
        self._lastRunTime = 0
        self.abort = False
        self._action = action

    def start(self, delayBeforeFirstRunSecs=0):
        '''
        Start the thread.

        @param delayBeforeFirstRunSecs: (int) Optional parameter which sets the
            initial delay before the first call to runAction().  If this is
            zero (the default), runAction() will be called immediately.
        '''
        if delayBeforeFirstRunSecs > 0:
            self._lastRunTime = (time.time() - self.runIntervalSecs +
                            delayBeforeFirstRunSecs)
        threading.Thread.start(self)

    def run(self):
        '''
        Thread runner.

        Called once when start() is called.  Loops indefinitely until
        self.abort is set.

        Put all significant code in runAction(), and leave this method alone.
        '''
        logger.debug(u'Thread %s is starting' % self.threadName)
        while not self.abort:
            if time.time() > (self._lastRunTime + self.runIntervalSecs):
                self._lastRunTime = time.time()
                try:
                    self.runAction()
                except Exception, e:
                    logger.error(u'Exception generated in thread %s: %s'
                                 % (self.threadName, e))
                    logger.debug(repr(traceback.format_exc()))

            if not self.abort:
                time.sleep(1)
        logger.debug(u'Thread %s is stopping' % self.threadName)

    def runAction(self):
        '''
        Override this method to perform needed functionality (if 'action' param
        is not passed to the constructor).

        This will be called every runIntervalSecs (if possible).  If a call
        takes longer than runIntervalSecs, the next call will be delayed until
        the previous has finished.

        Before starting (and during) any long-running operation, be sure to
        check the value of self.abort.  If this is set, the method must return
        immediately.  (as this generally means XMBC is shutting down).

        Note: you can access self.abort in other modules by checking
            threading.currentThread().abort
        (or, alternatively, check xbmc.abortRequested)
        '''
        if self._action is not None:
            self._action()
