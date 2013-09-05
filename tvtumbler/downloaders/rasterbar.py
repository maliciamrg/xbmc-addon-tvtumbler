'''
This file is part of TvTumbler.

Created on Aug 30, 2013

http://www.rasterbar.com/products/libtorrent/manual.html

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
from .. import logger, utils
from .torrent import TorrentDownloader, TorrentDownload
from ..schedule import SchedulerThread
import os
import shutil
import sys
import time
import traceback
import xbmc
import xbmcvfs

LIBTORRENT_AVAILABLE = False
LIBTORRENT_FAILURE_REASON = None
try:
    import libtorrent as lt
    if (lt.version_major, lt.version_minor) < (0, 16):
        LIBTORRENT_FAILURE_REASON = (u'The version of libtorrent you have installed '
                                     u'"%s", is too old for use with tvtumbler.  '
                                     u'Version 0.16 or later required.') % (lt.version,)
        logger.notice(LIBTORRENT_FAILURE_REASON)
    else:
        logger.notice('libtorrent import succeeded, libtorrent is available')
        LIBTORRENT_AVAILABLE = True
except ImportError, e:
    LIBTORRENT_FAILURE_REASON = 'libtorrent import failed, functionality will not be available: ' + str(e)
    logger.notice(LIBTORRENT_FAILURE_REASON)

__addon__ = sys.modules["__main__"].__addon__

# the number of seconds we wait after adding a torrent to see signs of download beginning
TORRENT_START_WAIT_TIMEOUT_SECS = 120

# The actual running lt session.  Obtain it by calling _get_session() - which
# will create it if needed.
_lt_sess = None


class LibtorrentDownloader(TorrentDownloader):

    def __init__(self):
        '''Private Xtor.  Overridden here so that we can create a polling thread'''
        super(TorrentDownloader, self).__init__()
        self._poller = SchedulerThread(action=self._poll,
                               threadName=self.__class__.__name__,
                               runIntervalSecs=3)

    def _poll(self):
        # @todo: pop any libtorrent messages
        sess = self._get_session(createIfNeeded=False)
        while sess:
            a = sess.pop_alert()
            if not a:
                break

            if type(a) == str:
                logger.debug(a)
            else:
                logger.debug(u'(%s): %s' % (type(a).__name__, str(a.message())))

    @classmethod
    def is_available(cls):
        return LIBTORRENT_AVAILABLE

    @classmethod
    def is_enabled(cls):
        return (__addon__.getSetting('libtorrent_enable') == 'true')

    def download(self, downloadable):
        '''
        Override in your derived class.
        Be sure to add the 'Download' to _running_downloads.

        @param downloadable: What we want to download.
        @type downloadable: Downloadable
        @return: Boolean value indicating success.
        @rtype: bool
        '''
        rd = LibtorrentDownload(downloadable, self)
        key = rd.key
        if key in self._running_downloads:
            logger.notice('%s is already downloading!' % (key,))
            return False
        if rd.start():
            self._running_downloads[key] = rd
            if not self._poller.is_alive():
                self._poller.start(delayBeforeFirstRunSecs=2)
            return True
        return False

    @classmethod
    def _get_session(cls, createIfNeeded=True):
        global _lt_sess
        if _lt_sess is None and createIfNeeded:
            _lt_sess = lt.session()
            # _lt_sess.set_download_rate_limit(sickbeard.LIBTORRENT_MAX_DL_SPEED * 1024)
            # _lt_sess.set_upload_rate_limit(sickbeard.LIBTORRENT_MAX_UL_SPEED * 1024)

            settings = lt.session_settings()
            # settings.user_agent = 'sickbeard_bricky-%s/%s' % (version.SICKBEARD_VERSION.replace(' ', '-'), lt.version)
            # settings.rate_limit_utp = True  # seems this is rqd, otherwise uTP connections don't obey the rate limit

            settings.active_downloads = 8
            settings.active_seeds = 12
            settings.active_limit = 20
            settings.share_ratio_limit = 0.1  # for test.  use >1 in real life
            settings.seed_time_limit = 60 * 60 * 24  # don't seed for longer than a day

            # _lt_sess.listen_on(sickbeard.LIBTORRENT_PORT_MIN, sickbeard.LIBTORRENT_PORT_MAX)
            _lt_sess.set_settings(settings)
            _lt_sess.set_alert_mask(lt.alert.category_t.error_notification |
                                    # lt.alert.category_t.port_mapping_notification |
                                    lt.alert.category_t.storage_notification |
                                    # lt.alert.category_t.tracker_notification |
                                    lt.alert.category_t.status_notification |
                                    # lt.alert.category_t.port_mapping_notification |
                                    lt.alert.category_t.performance_warning
                                    )
            try:
                state = {}  # @todo: save/restore this
                _lt_sess.start_dht(state)
                _lt_sess.add_dht_router('router.bittorrent.com', 6881)
                _lt_sess.add_dht_router('router.utorrent.com', 6881)
                _lt_sess.add_dht_router('router.bitcomet.com', 6881)
            except Exception, ex:
                # just ignore any dht errors, this is just for bootstrapping
                logger.notice(u'Exception starting dht: ' + str(ex))

        return _lt_sess

    @classmethod
    def get_libtorrent_working_dir(cls, ensure_exists=False):
        """
        Get the working dir for libtorrent (an os path)
        """
        profile_path = xbmc.translatePath(__addon__.getAddonInfo('profile').decode('utf-8'))
        lt_working_dir = os.path.join(profile_path, 'libtorrent')
        if ensure_exists and not xbmcvfs.exists(lt_working_dir):
            logger.notice(u'Creating path: %s' % lt_working_dir)
            xbmcvfs.mkdir(lt_working_dir)

        return lt_working_dir

    @classmethod
    def get_libtorrent_download_dir(cls, ensure_exists=False):
        dir_path = os.path.join(cls.get_libtorrent_working_dir(ensure_exists), 'data')
        if ensure_exists and not xbmcvfs.exists(dir_path):
            logger.notice(u'Creating path: %s' % dir_path)
            xbmcvfs.mkdir(dir_path)

        return dir_path


class LibtorrentDownload(TorrentDownload):
    '''
    An actual running libtorrent download.
    '''

    @property
    def name(self):
        '''Override so that we can use the name from the torrent when we have it.'''
        try:
            return self._torrent_info.name()
        except AttributeError:
            try:
                return self._name
            except AttributeError:
                return super(LibtorrentDownload, self).name

    @property
    def total_size(self):
        try:
            return self._torrent_info.total_size()
        except AttributeError:
            try:
                return self._total_size
            except AttributeError:
                return super(LibtorrentDownload, self).total_size

    def get_downloaded_size(self):
        '''
        In bytes

        @rtype: int
        '''
        try:
            self._total_done
        except AttributeError:
            return 0

    def get_download_speed(self):
        '''
        In bytes/sec

        @rtype: float
        '''
        try:
            return self._download_payload_rate
        except AttributeError:
            return 0.0

    def get_upload_speed(self):
        '''
        In bytes/sec

        @rtype: float
        '''
        try:
            return self._upload_payload_rate
        except AttributeError:
            return 0.0

    def get_uploaded_size(self):
        '''In bytes.

        @rtype: int
        '''
        try:
            return self._all_time_upload
        except AttributeError:
            return 0

    def get_ratio(self):
        try:
            currentRatio = 0.0 if self._all_time_download == 0 else float(self._all_time_upload) / float(self._all_time_download)
            return currentRatio
        except AttributeError:
            return 0.0

    def _update_stats(self):
        '''
        Called (by _poll) every three seconds during download.
        Use this method to update stats, status etc.

        It is important that you *do* update the self._status field here (or override the
        get_status(), get_downloaded_size() and get_download_speed() methods to update
        when called), otherwise none of the on_status_change() or _on_* methods will fire.
        '''
        try:
            handle = self._handle
        except AttributeError:
            # No handle yet?  We've run too early.
            # Just fail silenty.
            return

        if not handle.is_valid():
            logger.error(u'Torrent handle is no longer valid.')
            self._status = self.FAILED
            return

        s = handle.status()
        if s.paused:
            self._status = self.PAUSED
        elif s.state in [lt.torrent_status.queued_for_checking,
                       lt.torrent_status.checking_files,
                       lt.torrent_status.downloading_metadata,
                       lt.torrent_status.allocating,
                       lt.torrent_status.checking_resume_data]:
            self._status = self.STARTING
        elif s.state is lt.torrent_status.downloading:
            self._status = self.DOWNLOADING
        elif s.state is lt.torrent_status.finished:
            self._status = self.FINISHED
        elif s.state is lt.torrent_status.seeding:
            self._status = self.POST_DOWNLOAD
        else:
            logger.notice(u'Unknown state %s.  Ignoring.' % (repr(s.state)))

        self._download_payload_rate = s.download_payload_rate
        self._upload_payload_rate = s.upload_payload_rate
        self._num_connected_peers = s.num_peers
        self._list_seeds = s.list_seeds
        self._list_peers = s.list_peers
        self._total_done = s.total_done
        self._all_time_download = s.all_time_download
        self._all_time_upload = s.all_time_upload

    def remove_files(self):
        '''
        Do whatever is necessary to remove any downloaded files.
        '''
        self.stop(deleteFilesTo=True)  # if the torrent is still in the session, this will delete also
        try:
            # but we try to make sure that the files are really deleted - just in case
            the_files = os.path.join(self.downloader.get_libtorrent_download_dir(False),
                                   self.name)
            shutil.rmtree(the_files)
        except Exception:
            pass

    @staticmethod
    def _torrent_has_any_media_files(torrent_info):
        """
        Internal function to check if a torrent has any useful media files.
        @param torrent_info: (a libtorrent torrent_info object)
        @return: (bool) True if any useful media is found, false otherwise.
        """
        for f in torrent_info.files():
            if utils.is_video_file(f.path):
                return True
        return False

    def start(self):
        '''
        Start a download
        '''
        if not super(LibtorrentDownload, self).start():
            return False

        self._status = self.STARTING
        try:
            sess = self.downloader._get_session()
            atp = {}  # add_torrent_params
            atp["save_path"] = self.downloader.get_libtorrent_download_dir(True)
            atp["storage_mode"] = lt.storage_mode_t.storage_mode_sparse
            atp["paused"] = False
            atp["auto_managed"] = True
            atp["duplicate_is_error"] = True
            self._have_torrentFile = False
            self._checkedForMedia = False
            magnet_link = self.download.get_magnet()
            if (magnet_link):
                logger.debug(u'Adding torrent to session: %s' % (magnet_link,))
                atp["url"] = magnet_link
            else:
                torrent = self.download.get_torrent()
                if torrent is None:
                    logger.notice('No valid torrent from %s, failing.' % (repr(self.download),))
                    self._status = self.FAILED
                    return False
                e = lt.bdecode(torrent)
                self._torrent_info = lt.torrent_info(e)
                logger.debug(u'Adding torrent to session: %s' % (self.name,))
                self._have_torrentFile = True

                try:
                    atp["resume_data"] = open(os.path.join(atp["save_path"],
                                                           self.name + '.fastresume'), 'rb').read()
                except:
                    pass

                if not self._torrent_has_any_media_files(self._torrent_info):
                    logger.notice(u'The torrent %s has no media files.  Not downloading.' % (self.name,))
                    self._status = self.FAILED
                    return False
                else:
                    self._checkedForMedia = True

                atp["ti"] = self._torrent_info

            self._start_time = time.time()
            self._handle = sess.add_torrent(atp)

            self._handle.set_max_connections(128)
            self._handle.set_max_uploads(-1)

            startedDownload = False
            while not startedDownload:
                time.sleep(0.5)

                if not self._handle.is_valid():
                    logger.notice(u'Torrent handle is no longer valid.')
                    self._status = self.FAILED
                    return False

                s = self._handle.status()

                if self._handle.has_metadata():
                    self._torrent_info = self._handle.get_torrent_info()

                    if not self._checkedForMedia:
                        # Torrent has metadata, but hasn't been checked for valid media yet.  Do so now.
                        if not self._torrent_has_any_media_files(self._torrent_info):
                            logger.notice(u'Torrent %s has no media files! Deleting it.' % (self.name))
                            self._status = self.FAILED
                            return False
                        self._checkedForMedia = True
                    self._update_stats()
                    if s.state in [lt.torrent_status.seeding,
                                   lt.torrent_status.downloading,
                                   lt.torrent_status.finished,
                                   lt.torrent_status.downloading_metadata]:
                        logger.info(u'Torrent "%s" has state "%s" (%s), interpreting as snatched' % (self.name,
                                                                                                     s.state,
                                                                                                     repr(s.state)))
                        # no need to update the _status here, _update_stats() will have done it above.
                        return True
                elif s.state is lt.torrent_status.downloading_metadata and magnet_link:
                    # if it's a magnet, 'downloading_metadata' is considered a success
                    logger.info(u'Torrent has state downloading_metadata, interpreting as snatched')
                    # no need to update the _status here, _update_stats() will have done it above.
                    return True
                else:
                    # no metadata and not a magnet?  Definitely not started yet then!
                    pass

                # check for timeout
                if time.time() - self._start_time > TORRENT_START_WAIT_TIMEOUT_SECS:
                    logger.notice(u'Torrent has failed to start within timeout %d secs.  Removing' %
                                        (TORRENT_START_WAIT_TIMEOUT_SECS))
                    self._status = self.FAILED
                    return False

        except Exception, e:
            logger.error('Error trying to download via libtorrent: ' + str(e))
            logger.debug(traceback.format_exc())
            self._status = self.FAILED
            return False

    def stop(self, deleteFilesToo=True):
        sess = self.downloader._get_session()
        try:
            handle = self._handle
        except AttributeError:
            logger.notice('attempt to stop torrent with no handle set?')
            return

        if not handle.is_valid():
            logger.error(u'Torrent handle is no longer valid.')
            self._status = self.FAILED
            return

            try:
                fr_file = os.path.join(self.downloader.get_libtorrent_download_dir(False),
                                       self.name + '.fastresume')
                os.remove(fr_file)
            except Exception:
                pass
            sess.remove_torrent(handle, 1 if deleteFilesToo else 0)
            del self._handle
            self._status = self.FINISHED
