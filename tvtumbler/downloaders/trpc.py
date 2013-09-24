'''
This file is part of TvTumbler.

Created on Aug 30, 2013

http://pythonhosted.org/transmissionrpc/

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
from .. import logger, utils, events
from .torrent import TorrentDownloader, TorrentDownload
import os
import sys
import time
import traceback
import xbmc
import xbmcvfs
import transmissionrpc
import base64

__addon__ = sys.modules["__main__"].__addon__

# the number of seconds we wait after adding a torrent to see signs of download beginning
TORRENT_START_WAIT_TIMEOUT_SECS = 120

# The actual running transmission rpc client.  Obtain it by calling _get_client() - which
# will create it if needed.
_trcp_client = None


def _on_settings_change():
    if TRPCDownloader.is_enabled():
        logger.debug('Settings have changed, checking if TRPC settings are ok')
        isok, reason = TRPCDownloader.check_settings()
        logger.debug('Got: ' + str(reason))
        if not isok:
            logger.notice('config check failed on TRPC: ' + str(reason))
            __addon__.setSetting(id='trpc_enable', value='false')
            xbmc.executebuiltin('Notification(%s,%s,60000,%s)' % ('TvTumbler: Transmission',
                                                                  reason,
                                                                  'DefaultIconError.png'))

events.add_event_listener(events.SETTINGS_CHANGED, _on_settings_change)


class TRPCDownloader(TorrentDownloader):

    def __init__(self):
        '''Private Xtor.  Overridden here so that we can create a polling thread'''
        super(TorrentDownloader, self).__init__()

    @classmethod
    def get_name(cls):
        '''
        Human-readable name.
        @rtype: str
        '''
        return 'Transmission'

    @classmethod
    def is_available(cls):
        return True

    @classmethod
    def is_enabled(cls):
        return (__addon__.getSetting('trpc_enable') == 'true')

    @classmethod
    def get_download_class(cls):
        return TRPCDownload

    @classmethod
    def _get_client(cls, createIfNeeded=True):
        global _trcp_client
        if _trcp_client is None and createIfNeeded:
            trpc_host = __addon__.getSetting('trpc_host')
            trpc_port = int(__addon__.getSetting('trpc_port'))
            trpc_user = __addon__.getSetting('trpc_user').decode('utf-8')
            trpc_pass = __addon__.getSetting('trpc_pass').decode('utf-8')

            if trpc_user == '':
                trpc_user = None

            if trpc_pass == '':
                trpc_pass = None

            _trcp_client = transmissionrpc.Client(address=trpc_host,
                                                  port=trpc_port,
                                                  user=trpc_user,
                                                  password=trpc_pass)

            session = _trcp_client.get_session()  # @UnusedVariable
            # @todo: settings for the client/session should go here
            if cls.running_locally():
                _trcp_client.set_session(download_dir=cls.get_download_dir())

        return _trcp_client

    def on_download_downloaded(self, download):
        '''Called when the download has completed (i.e. no more data).

        We override the BaseDownloader implementation here because sometimes
        transmission reports that it has finished a download before all the files
        are actually available in the download dir.
        So we delay a little while if that happens.
        '''
        delay_needed = True
        total_delayed = 0
        while delay_needed and total_delayed <= 60000:
            delay_needed = False
            for f in download.get_files():
                if not xbmcvfs.exists(f):
                    logger.debug(u'Downloader reported that file "%s" is downloaded, but it cannot '
                                  u'be found.' % (f,))
                    delay_needed = True
                    break
            if delay_needed:
                logger.debug(u'Waiting 10 seconds ...')
                xbmc.sleep(10000)
                total_delayed += 10000

        super(TRPCDownloader, self).on_download_downloaded(download)  # call the base class implmentation

    @classmethod
    def get_download_dir(cls, ensure_exists=False):
        '''
        Get the configured Transmission download directory.

        @param ensure_exists: Ignored
        @type ensure_exists: bool
        @return: The full path, either a remote path with a protocol (e.g. 'smb://192.168.1.1/share/') or a local
            path without one (e.g. '/temp/downloads/')
        @rtype: str
        '''
        return xbmc.translatePath(__addon__.getSetting('trpc_ddir').decode('utf-8'))

    @classmethod
    def running_locally(cls):
        '''
        Is XBMC configured to connect to a locally running transmission? (i.e. on the same host)

        @rtype: bool
        '''
        return __addon__.getSetting('trpc_host') == '127.0.0.1'

    @classmethod
    def check_settings(cls):
        # host, port, and ddir absolutely must be specified.
        _host = __addon__.getSetting('trpc_host')
        if not _host:
            return False, 'Host (ip address) is missing'

        _port = __addon__.getSetting('trpc_port')
        if not _port or _port == "0":
            return False, 'Invalid Port'

        _ddir = cls.get_download_dir()
        if not _ddir:
            return False, 'Download Dir is required.'

        # the download dir must exist
        if not xbmcvfs.exists(_ddir):
            return False, 'Download Dir not found.'

        # if transmission is running locally, the os must be able to resolve the download dir path
        if cls.running_locally() and not os.path.exists(_ddir):
            return False, 'Download Dir must be a local path when transmission is running locally.'

        trpc_user = __addon__.getSetting('trpc_user').decode('utf-8')
        trpc_pass = __addon__.getSetting('trpc_pass').decode('utf-8')

        try:
            transmissionrpc.Client(address=_host, port=_port,
                                   user=trpc_user, password=trpc_pass)
        except:
            (e_type, e, traceback) = sys.exc_info()

            reason = 'Unexpected Error: ' + str(e)
            if e_type is transmissionrpc.TransmissionError:
                if e.original:
                    if e.original.code is 401:
                        reason = 'Invalid Username or Password'
                    else:
                        reason = 'Unable to Connect'
            elif type is ValueError:
                # In python 2.4, urllib2.HTTPDigestAuthHandler will barf up a lung
                # if auth fails and the server wants non-digest authentication
                reason = 'Invalid Username or Password'

            return False, reason

        # success if we get to here
        return True, 'Success'

    def on_download_finished(self, download):
        '''Override here so that we can catch the last download finishing and destroy the client connection'''
        global _trcp_client
        super(TRPCDownloader, self).on_download_finished(download)
        if len(self._running_downloads) == 0:
            logger.info('The last trpc download has finished.  Destroying client.')
            _trcp_client = None


class TRPCDownload(TorrentDownload):
    '''
    An actual running transmission rpc download.
    '''

    @property
    def name(self):
        '''Override so that we can use the name from the torrent when we have it.'''
        try:
            return self._torrent.name
        except AttributeError:
            return super(TRPCDownload, self).name

    @property
    def total_size(self):
        try:
            return self._torrent.sizeWhenDone
        except AttributeError:
            return super(TRPCDownload, self).total_size

    def get_downloaded_size(self):
        '''
        In bytes

        @rtype: int
        '''
        try:
            return self._torrent.downloadedEver
        except AttributeError:
            return 0

    def get_download_speed(self):
        '''
        In bytes/sec

        @rtype: float
        '''
        try:
            return self._torrent.rateDownload
        except AttributeError:
            return 0.0

    def get_upload_speed(self):
        '''
        In bytes/sec

        @rtype: float
        '''
        try:
            return self._torrent.rateUpload
        except AttributeError:
            return 0.0

    def get_uploaded_size(self):
        '''In bytes.

        @rtype: int
        '''
        try:
            return self._torrent.uploadedEver
        except AttributeError:
            return 0

    def get_ratio(self):
        try:
            return self._torrent.ratio
        except AttributeError:
            return 0.0

    def start(self):
        '''
        Start a download
        '''
        if not super(TRPCDownload, self).start():
            return False

        self._status = self.STARTING
        try:
            client = self.downloader._get_client()
            self._have_torrentFile = False
            self._checkedForMedia = False
            magnet_link = self.downloadable.get_magnet()
            if (magnet_link):
                logger.debug(u'Adding torrent to session: %s' % (magnet_link,))
                torrent = magnet_link
            else:
                torrent = self.downloadable.get_torrent()
                if torrent is None:
                    logger.notice('No valid torrent from %s, failing.' % (repr(self.downloadable),))
                    self._status = self.FAILED
                    return False

                try:
                    # transmissionrpc expects a base64 encoded torrent (not really sure why though?)
                    torrent = base64.b64encode(torrent)
                except UnicodeEncodeError, ue:
                    logger.error('Unable to base 64 encode a torrent: ' + str(ue))
                    logger.debug(repr(torrent))

                self._have_torrentFile = True

            # transmissionrpc fails rather cryptically when you try to add a torrent that it
            # is already downloading.  So the safest thing here is to check if there's already
            # a torrent with the hash we have.
            infohash = self.downloadable.infohash
            if infohash:
                try:
                    infohash = infohash.lower()  # transmission uses lowercase hashes
                    logger.debug('checking for already-running torrent with hash: ' + infohash)
                    client.get_torrent(infohash)  # will raise a 'KeyError' on failure
                    logger.notice('Failed to add torrent - transmission already has a torrent with this hash')
                    self._status = self.FAILED
                    return False
                except KeyError:
                    logger.debug('no already running torrent with this hash')

            self._start_time = time.time()
            if self.downloader.running_locally():
                # when we're running locally, we pass in the download dir to tranmission
                self._torrent = client.add_torrent(torrent=torrent,
                                                   download_dir=self.downloader.get_download_dir())
            else:
                # and when we're not, we can't.  We just have to trust the user to set it up right
                self._torrent = client.add_torrent(torrent)

            startedDownload = False
            while not startedDownload:
                xbmc.sleep(500)

                self._torrent.update()

                if self._torrent.metadataPercentComplete == 1.0:
                    if not self._checkedForMedia:
                        # Torrent has metadata, but hasn't been checked for valid media yet.  Do so now.
                        if not self._torrent_has_any_video_files(self._torrent):
                            logger.notice(u'Torrent %s has no video files! Deleting it.' % (self.name))
                            client.remove_torrent([self._torrent.id], delete_data=True)
                            self._status = self.FAILED
                            return False
                        self._checkedForMedia = True

                current_status = self._torrent.status
                if ((current_status in ['download pending', 'downloading', 'seed pending', 'seeding']) or
                    (current_status == 'stopped' and self._torrent.isFinished)):
                    logger.info(u'Torrent "%s" has state "%s", interpreting as snatched' % (self.name,
                                                                                            current_status))
                    return True

                # check for timeout
                if time.time() - self._start_time > TORRENT_START_WAIT_TIMEOUT_SECS:
                    logger.notice(u'Torrent has failed to start within timeout %d secs.  Removing' %
                                        (TORRENT_START_WAIT_TIMEOUT_SECS))
                    client.remove_torrent([self._torrent.id], delete_data=True)
                    self._status = self.FAILED
                    return False

        except Exception, e:
            logger.error('Error trying to download via transmissionrpc: ' + str(e))
            logger.debug(traceback.format_exc())
            try:
                client.remove_torrent([self._torrent.id], delete_data=True)
            except AttributeError:
                pass  # no self._torrent, error can be safely ignored
            self._status = self.FAILED
            return False

    def _update_stats(self):
        '''
        Called (by _poll) every three seconds during download.
        Use this method to update stats, status etc.

        It is important that you *do* update the self._status field here (or override the
        get_status(), get_downloaded_size() and get_download_speed() methods to update
        when called), otherwise none of the on_status_change() or _on_* methods will fire.
        '''
        try:
            torrent = self._torrent
        except AttributeError:
            # No _torrent yet?  We've run too early.
            # Just fail silenty.
            return

        try:
            torrent.update()
        except KeyError, ke:
            # transmissionrpc currently throws a KeyError when the torrent
            # is invalid.  Treat this as a failure.
            logger.error(u'Error from transmission, assuming torrent failed: ' + str(ke))
            self._status = self.FAILED
            return

        s = torrent.status
        if s in ['check pending',
                 'checking',
                 'download pending']:
            self._status = self.STARTING
        elif s == 'downloading':
            self._status = self.DOWNLOADING
        elif s == 'stopped':
            if self._torrent.isFinished:
                self._status = self.FINISHED
            else:
                self._status = self.PAUSED
        elif s == 'seeding':
            self._status = self.POST_DOWNLOAD
        else:
            logger.notice(u'Unknown state %s.  Ignoring.' % (s))

        if not self._checkedForMedia and torrent.metadataPercentComplete == 1.0:
            # Torrent has metadata, but hasn't been checked for valid media yet.  Do so now.
            if not self._torrent_has_any_video_files(self._torrent):
                logger.notice(u'Torrent %s has no video files! Deleting it.' % (self.name))
                self.downloader._get_client().remove_torrent([self._torrent.id], delete_data=True)
                self._status = self.FAILED
                return False
            self._checkedForMedia = True

    def remove_files(self):
        '''
        Do whatever is necessary to remove any downloaded files.
        '''
        self.stop(deleteFilesToo=True)  # if the torrent is still in the session, this will delete also

    def get_files(self):
        '''
        Get a list of downloaded files (full paths).

        @rtype: [str]
        '''
        if self.get_status() & self.DOWNLOADED_STATE:
            ddir = self.downloader.get_download_dir()
            return [os.path.join(ddir, v['name']) for v in self._torrent.files().itervalues()]
        else:
            return []

    @staticmethod
    def _torrent_has_any_video_files(torrent):
        """
        Internal function to check if a torrent has any useful media files.

        @param torrent: (a torrent reference)
        @type torrent: transmissionrpc.Torrent
        @return: (bool) True if any useful media is found, false otherwise.
        """
        for f in torrent.files().itervalues():
            if utils.is_video_file(f['name']):
                logger.debug('File "%s" in torrent "%s" is a video file' % (f['name'], torrent.name))
                return True
        logger.info('Iterated over all the files in "%s" and found no video files.' % (torrent.name,))
        return False

    def stop(self, deleteFilesToo=True):
        client = self.downloader._get_client()
        client.remove_torrent(self._torrent.id, delete_data=deleteFilesToo)
        del self._torrent
        self._status = self.FINISHED
