'''
This file is part of TvTumbler.

Created on Aug 30, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
from ..schedule import SchedulerThread


class BaseDownloader(object):
    '''Base class for all downloaders'''

    def __init__(self):
        '''Private Xtor.  Use get_instance() instead.'''
        self._current_ptr = 0
        self._running_downloads = {}
        self._poller = SchedulerThread(action=self._poll,
                                       threadName=self.__class__.__name__,
                                       runIntervalSecs=3)

    @classmethod
    def get_instance(cls):
        '''Get the singleton instance of this class.

        @return: The singleton instance of this class
        @rtype: cls
        '''
        try:
            return cls._instance
        except AttributeError:
            cls._instance = cls()
            return cls._instance

    @classmethod
    def is_available(cls):
        '''
        Is this downloader available?
        (i.e. could it operate if enabled)

        @rtype: bool
        '''
        return False

    @classmethod
    def is_enabled(cls):
        '''
        Is this downloader enabled?
        (i.e. willing to accept downloads)

        @rtype: bool
        '''
        return False

    def __iter__(self):
        '''
        Makes this class iterable.
        (i.e. you can iterate over an instance of this class to get its running downloads)
        '''
        return self

    def next(self):
        '''Return the next Download'''
        if self._current_ptr >= len(self._running_downloads):
            raise StopIteration
        else:
            self._current_ptr += 1
            return self._running_downloads[self._current_ptr - 1]

    def __len__(self):
        '''Implements len().

        @return: Returns the number of currently running downloads
        @rtype: int
        '''
        return len(self._running_downloads)

    def __getitem__(self, key):
        '''Key access to the running downloads.
        Returns a RunningDownload by its key.

        @param key: Key of a RunningDownload
        @type key: str
        @return: Returns a RunningDownload if one with a matching key exists, raises a KeyError otherwise.
        @rtype: RunningDownload
        '''
        return self._running_downloads[key]

    def add(self, downloadable):
        '''
        Override in your derived class.
        Be sure to start the self._poller if needed (i.e. add was successful,
        and it's not already running), and add the 'Download' to
        _running_downloads.

        @param downloadable: What we want to download.
        @type downloadable: Downloadable
        @return: Boolean value indicating success.
        @rtype: bool
        '''
        # Sample Implementation:
        # if not self._poller.is_alive():
        #     self._poller.start(delayBeforeFirstRunSecs=5)
        # rd = Download(downloadable)
        # if rd.start():
        #     self._running_downloads[rd.key] = rd
        #     return True
        return False

    def remove(self, key):
        rd = self._running_downloads[key]
        rd.stop(delete_files=True)
        del rd

    def _poll(self):
        '''
        Called by self._poller every 2 secs while we have a download running.
        Responsible for stopping itself when there are no more downloads.

        Override this and call this implementation in your derived class.

        @return: Returns False if the poller was aborted, true otherwise
        @rtype: bool
        '''
        if len(self._running_downloads) == 0:
            self._poller.abort = True
            return False

        for (k, d) in self._running_downloads:
            old_status = d.get_status()
            d.update_stats()
            new_status = d.get_status()
            if old_status != new_status:
                d.on_status_change(old_status, new_status)

        return True


class Download(object):
    '''
    An in-process download.
    '''

    # Possible status values returned by get_status()
    FAILED = 1 << 15  # Any permanent failure
    NOT_STARTED = 1  # Initial state
    STARTING = 1 << 1  # Received start instruction, but no data yet
    DOWNLOADING = 1 << 2  # Currently receiving data
    PAUSED = 1 << 3  # Started successfully, but not currently downloading
    POST_DOWNLOAD = 1 << 4  # Download completed, carrying out post-download activity (e.g. seeding)
    FINISHED = 1 << 5  # Complete - no further traffic

    _status_names = {FAILED: 'Failed',
                     NOT_STARTED: 'Not Started',
                     STARTING: 'Starting',
                     DOWNLOADING: 'Downloading',
                     PAUSED: 'Paused',
                     POST_DOWNLOAD: 'Post Download',
                     FINISHED: 'Finished'}

    # composites
    FINAL_STATE = FINISHED | FAILED
    RUNNING_STATE = STARTING | DOWNLOADING | POST_DOWNLOAD
    DOWNLOADED_STATE = POST_DOWNLOAD | FINISHED

    def __init__(self, downloadable):
        '''
        XTor.

        @param downloadable: the Downloadable we're downloading.
        @type downloadable: Downloadable
        '''
        self._downloadable = downloadable
        self._status = self.NOT_STARTED

    @property
    def key(self):
        return self._downloadable.unique_key

    @property
    def name(self):
        return self._downloadable.name

    def get_status_text(self):
        '''
        Return a text description of the current status.
        (for gui representation)

        @return: Simple text (preferably one word) e.g. 'Running', 'Paused', 'Failed' etc.
        @rtype: str
        '''
        try:
            return self._status_names[self.get_status()]
        except KeyError:
            return 'Unknown'

    def get_status(self):
        '''
        Get the current status of the download.
        Returns one of the status constants.
        @rtype: int
        '''
        return self._status

    @property
    def total_size(self):
        '''
        In bytes

        @rtype: int
        '''
        return 0

    def get_downloaded_size(self):
        '''
        In bytes

        @rtype: int
        '''
        return 0

    def get_download_speed(self):
        '''
        In bytes/sec

        @rtype: float
        '''
        return 0.0

    def update_stats(self):
        '''
        Called (by the downloader) every two seconds during download.
        Use this method to update stats, status etc.

        It is important that you *do* update the self._status field here (or override the
        get_status(), get_downloaded_size() and get_download_speed() methods to update
        when called), otherwise none of the on_status_change() or _on_* methods will fire.
        '''
        pass

    def on_status_change(self, old_status, new_status):
        '''
        Called (by the downloader) when the status changes.
        You can override this method and use your own handling, or leave this
        implementation and handle all significant changes in the _on_* methods
        that this implementation calls.
        '''
        if old_status == self.NOT_STARTED and new_status != self.NOT_STARTED:
            self._on_started()

        if new_status == self.FAILED and old_status != self.FAILED:
            self._on_failed()

        try:
            prev_downloaded = self.on_status_change._prev_downloaded
            if prev_downloaded == 0 and self.get_downloaded_size():
                self._on_first_data()
        except AttributeError:
            pass
        self.on_status_change._prev_downloaded = self.get_downloaded_size()

        if new_status == self.PAUSED and old_status != self.PAUSED:
            self._on_paused()
        elif old_status == self.PAUSED and new_status != self.PAUSED:
            self._on_resumed()

        if (new_status & self.DOWNLOADED_STATE) and not (old_status & self.DOWNLOADED_STATE):
            self._on_downloaded()

        if new_status == self.FINISHED and old_status != self.FINISHED:
            self._on_finished()

    def _on_started(self):
        '''Called by on_status_change()'''
        pass

    def _on_first_data(self):
        '''Called by on_status_change()'''
        pass

    def _on_paused(self):
        '''Called by on_status_change()'''
        pass

    def _on_resumed(self):
        '''Called by on_status_change()'''
        pass

    def _on_downloaded(self):
        '''Called by on_status_change()'''
        pass

    def _on_finished(self):
        '''Called by on_status_change()'''
        pass

    def _on_failed(self):
        '''Called by on_status_change()'''
        pass



