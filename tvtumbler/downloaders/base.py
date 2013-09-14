'''
This file is part of TvTumbler.

Created on Aug 30, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
from ..schedule import SchedulerThread
from .. import logger
from . import on_download_failed, on_download_downloaded


class BaseDownloader(object):
    '''Base class for all downloaders.

    Lifecycle of a download:
    1. Ask something that inherits from this class if it can handle your download: cls.can_download()
    2. Get an instance of it: d = cls.get_instance(downloadable)
    3. Tell it to start the download: started = d.download(downloadable)
    4. The download (if successful) will manage itself thereafter, calling:
           on_download_downloaded() when it finishes the download.
           on_download_finished() when it is truly finished (eg. after seeding)
           on_download_failed() if it fails.
       The default implementation of these is probably ok for most cases.
    '''

    def __init__(self):
        '''Private Xtor.  Use get_instance() instead.'''
        self._running_downloads = {}

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

    @classmethod
    def can_download(cls, downloadable):
        '''
        Can this downloader download this downloadable?
        Obviously you'll want to override this one.

        @return: True/False.  Generally a decision made on the class of downloadable.
        @rtype: bool
        '''
        return False

    @property
    def downloads(self):
        '''
        Get all running download for this downloader

        @rtype: [Download]
        '''
        return self._running_downloads.values()

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

    def download(self, downloadable):
        '''
        Override in your derived class.
        Be sure to add the 'Download' to _running_downloads.

        @param downloadable: What we want to download.
        @type downloadable: Downloadable
        @return: Boolean value indicating success.
        @rtype: bool
        '''
        # Sample Implementation:
        #
        # rd = Download(downloadable, self)
        # key = rd.key
        # if key in self._running_downloads:
        #     logger.notice('%s is already downloading!' % (key,))
        #     return False
        # if rd.start():
        #     self._running_downloads[key] = rd
        #     return True
        return False

    def on_download_failed(self, download):
        '''Called (by the download), when it fails.'''
        del self._running_downloads[download.key]
        on_download_failed(download)  # call the module implementation

    def on_download_downloaded(self, download):
        '''Called when the download has completed (i.e. no more data).

        Care here: we can't just delete at this point because the download
        may have future work (e.g. seeding).
        '''
        on_download_downloaded(download)  # call the module implementation

    def on_download_finished(self, download):
        '''Download is completely complete.'''
        if download.copied_to_library:
            download.remove_files()
        else:
            download.stop(deleteFilesToo=False)
        del self._running_downloads[download.key]


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

    def __init__(self, downloadable, downloader):
        '''
        XTor.

        @param downloadable: the Downloadable we're downloading.
        @type downloadable: Downloadable
        @param downloader: the Downloader to which this download belongs.
        @type downloader: BaseDownloader
        '''
        self._downloadable = downloadable
        self._downloader = downloader
        self._status = self.NOT_STARTED
        self._poller = SchedulerThread(action=self._poll,
                                       threadName=self.__class__.__name__,
                                       runIntervalSecs=3)
        self.copied_to_library = False


    @property
    def key(self):
        return self._downloadable.unique_key

    @property
    def name(self):
        return self._downloadable.name

    @property
    def downloader(self):
        return self._downloader

    @property
    def downloadable(self):
        return self._downloadable

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

    def start(self):
        '''
        Start the download.

        In your derived class, override this and call it from the overridden
        method (where you will also start whatever is needed to run the download).

        @return: True if the download begins successfully, false otherwise.
        @rtype: bool
        '''
        if self._status != self.NOT_STARTED:
            logger.notice('Attempt to start Download, but the status is %s.  Not starting' %
                          (self._status_names[self._status]))
            return False
        self._poller.start(2)
        return True

    def remove_files(self):
        '''
        Do whatever is necessary to remove any downloaded files.
        '''
        pass

    def get_files(self):
        '''
        Get a list of downloaded files (full paths).

        @rtype: [str]
        '''
        return []

    def _poll(self):
        '''
        Called by self._poller every 3 secs while we have a download running.
        Responsible for telling the downloader when the download is complete, and
        then for stopping the self._poller.

        The default implementation below calls on_status_change for any significant
        change, which in turns calls the appropriate _on_* method (which, for download
        complete, finished, or failure, in turns calls the downloader).

        You can override this method if it makes sense, but beware of the responsibility
        to notify the downloader.

        @return: Returns False if the poller was aborted, true otherwise
        @rtype: bool
        '''
        old_status = self.get_status()
        self._update_stats()
        new_status = self.get_status()
        if old_status != new_status:
            self._on_status_change(old_status, new_status)

        if self.get_status() & self.FINAL_STATE:
            logger.debug('Download has reached a final state.  Stopping poller.')
            self._poller.abort = True
            return False

        return True

    def _update_stats(self):
        '''
        Called (by _poll) every three seconds during download.
        Use this method to update stats, status etc.

        It is important that you *do* update the self._status field here (or override the
        get_status(), get_downloaded_size() and get_download_speed() methods to update
        when called), otherwise none of the on_status_change() or _on_* methods will fire.
        '''
        pass

    def _on_status_change(self, old_status, new_status):
        '''
        Called (by self._poller) when the status changes.
        You can override this method and use your own handling, or leave this
        implementation and handle all significant changes in the _on_* methods
        that this implementation calls.
        '''
        if old_status == self.NOT_STARTED and new_status != self.NOT_STARTED:
            self._on_started()

        if new_status == self.FAILED and old_status != self.FAILED:
            self._on_failed()
            self._downloader.on_download_failed(self)

        try:
            prev_downloaded = self._on_status_change._prev_downloaded
            if prev_downloaded == 0 and self.get_downloaded_size():
                self._on_first_data()
        except AttributeError:
            pass
        self._on_status_change.__func__._prev_downloaded = self.get_downloaded_size()

        if new_status == self.PAUSED and old_status != self.PAUSED:
            self._on_paused()
        elif old_status == self.PAUSED and new_status != self.PAUSED:
            self._on_resumed()

        if (new_status & self.DOWNLOADED_STATE) and not (old_status & self.DOWNLOADED_STATE):
            self._on_downloaded()
            self._downloader.on_download_downloaded(self)

        if new_status == self.FINISHED and old_status != self.FINISHED:
            self._on_finished()
            self._downloader.on_download_finished(self)

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

    @property
    def episodes(self):
        '''
        Get a list of episodes in this download (obtained from the downloadable)

        @rtype: [TvEpisode]
        '''
        return self._downloadable.episodes
