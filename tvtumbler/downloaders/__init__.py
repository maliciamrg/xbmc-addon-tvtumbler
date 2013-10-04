'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import os
import sys

import xbmc
import xbmcvfs

from .. import logger, utils, jsonrpc, events, numbering
from . import rasterbar, trpc


__addon__ = sys.modules["__main__"].__addon__
__addonname__ = sys.modules["__main__"].__addonname__

_enabled_downloaders = None


def _on_settings_changed():
    logger.debug('Settings changed, resetting enabled downloaders')
    global _enabled_downloaders
    _enabled_downloaders = None

events.add_event_listener(events.SETTINGS_CHANGED, _on_settings_changed)


def _on_abort_requested():
    logger.debug('Abort Requested.  Saving running status of active downloads')
    for dler in get_enabled_downloaders():
        dler.save_running_state()

events.add_event_listener(events.ABORT_REQUESTED, _on_abort_requested)


def get_enabled_downloaders():
    '''Get a list of enabled downloaders - higher priority ones first.

    @return: A list of downloaders - higher priority ones first.
    @rtype: [BaseDownloader]
    '''
    global _enabled_downloaders
    if _enabled_downloaders is None:
        _all_downloaders = [rasterbar.LibtorrentDownloader, trpc.TRPCDownloader]
        _enabled_downloaders = [ad.get_instance() for ad in _all_downloaders if ad.is_available() and ad.is_enabled()]
    return _enabled_downloaders


def download(downloadable):
    '''
    Start an actual download.
    This may block for a while until some indication that the download has begun
    occurs.

    @return: True if the download appears to have started correctly.  False otherwise.
    @rtype: bool
    '''
    logger.debug('------------------------------------------------------------')
    logger.notice('Received instruction to download: ' + repr(downloadable))
    logger.debug('------------------------------------------------------------')

    for d in get_enabled_downloaders():
        if d.can_download(downloadable):
            if d.download(downloadable):
                if (__addon__.getSetting('notify_snatch') == 'true'):
                    xbmc.executebuiltin('Notification(%s,%s,15000,%s)' % (downloadable.name,
                                                                          'Download Started',
                                                                          __addon__.getAddonInfo('icon')))
                return True

    logger.notice('No downloader accepted the download.  Sorry.')
    return False


def is_downloading(episode):
    '''
    Check if any downloader is currently downloading the episode.

    @param episode: The episode to check.
    @type episode: TvEpisode
    @return: If any downloader currently has this episode, returns True, False otherwise.
    @rtype: bool
    '''
    for dler in get_enabled_downloaders():
        for dl in dler.downloads:
            for ep in dl.downloadable.episodes:
                if ep == episode:
                    return True
    return False


def on_download_downloaded(download):
    '''
    Called when a download downloads.

    @todo: Most of this code would make much more sense in the BaseDownloader (which is the only thing that calls this
        anyway).  Move it there.

    @param download: The download that has downloaded.
    @type download: base.Download
    '''
    from .. import names

    logger.debug('------------------------------------------------------------')
    logger.notice('Download has downloaded: ' + repr(download))
    logger.debug('------------------------------------------------------------')
    tv_show_dir = download.downloadable.tvshow.get_path()
    all_tvdb_episodes = []
    for ep in download.episodes:
        for te in ep.tvdb_episodes:
            all_tvdb_episodes.append(te)  # this is a list of tuples (season, episode)
    all_tvdb_seasons = list(set([x[0] for x in all_tvdb_episodes]))
    feeder = download.downloadable.feeder  # care here: might be None
    name_parser = feeder.get_nameparser() if feeder else names.SceneNameParser
    source_numbering = feeder.get_numbering() if feeder else numbering.SCENE_NUMBERING
    any_files_copied = False
    has_known_video_file = False
    videos_in_download = []
    for f in download.get_files():
        if utils.is_video_file(f):
            if not xbmcvfs.exists(f):
                logger.notice(u'Downloader reported that file "%s" is downloaded, but it cannot '
                              u'be found.' % (f,))
                continue
            videos_in_download.append(f)

    for f in videos_in_download:
        np = name_parser(os.path.basename(f), has_ext=True,
                         numbering_system=source_numbering)
        
        if np.is_known:
            target_filename = np.make_local_filename(numbering=numbering.TVDB_NUMBERING)
            
            # if the filename is parsable, then we use the season for the first
            # episode in the filename (using tvdb numbering)
            season = np.episodes[0].tvdb_episodes[0][0]

            # quick safety check: if the filename triggered any of our 'bad' regexes,
            # then we had better ignore it.
            if np.is_bad:
                logger.notice(u'Downloaded file "%s" triggered a bad regex, not copying.' % (f,))
                continue

            has_known_video_file = True

        elif len(all_tvdb_seasons) == 1:
            if len(videos_in_download) == 1 and len(download.episodes) == 1:
                # this is the *only* video file in the download, and the download only has one episode.
                # So, even though we can't parse its name, we know what it is, so we can give it a sensible one.
                target_filename = download.episodes[0].fake_local_filename(use_numbering=numbering.TVDB_NUMBERING,
                                                                           extension=os.path.splitext(f)[1])
            else:
                # no option here but to use the original name and somehow hope that xbmc will work out what it is
                target_filename = os.path.basename(f)

            # file name is not parsable, but there is only one
            # season in this download, so we know where to put it.
            season = all_tvdb_seasons[0]
        else:
            logger.notice(u'Problem dealing with file %s after download. '
                          u'The download spans seasons, and we cannot work out the season '
                          u'for this particular file, so we don\'t know where to put it.' % (f,))
            continue

        dest_dir = os.path.join(tv_show_dir, 'Season %d' % (season,))
        if not xbmcvfs.exists(dest_dir + os.path.sep):  # xbmc requires the slash to know it's a dir
            xbmcvfs.mkdirs(dest_dir)
        dest_file = os.path.join(dest_dir, target_filename)
        logger.info(u'Copying file from "%s" to "%s".' % (f, dest_file))
        attempt = 1
        copied = False
        while attempt <= 5 and not copied:
            if xbmcvfs.copy(f, dest_file):
                logger.info('Success!')
                copied = True
                any_files_copied = True
                break
            else:
                logger.info('Failed to copy file.  Attempt %d' % (attempt))
                attempt = attempt + 1
                xbmc.sleep(5000)  # sometimes failure are temporary, give it a while and try again
    if any_files_copied:
        download.copied_to_library = True
        if (__addon__.getSetting('notify_download') == 'true'):
            xbmc.executebuiltin('Notification(%s,%s,15000,%s)' % (download.name,
                                                                  'Download Finished',
                                                                  __addon__.getAddonInfo('icon')))
        jsonrpc.videolibrary_scan(tv_show_dir)
    else:
        # No files copied.
        # If this is because there were no known video files in the download, then it's best to blacklist
        # the download also.
        if not has_known_video_file:
            logger.notice('No known video files in download.  Blacklisting: ' + repr(download.downloadable))
            download.downloadable.blacklist()
        xbmc.executebuiltin('Notification(%s,%s,60000,%s)' % (download.name,
                                                              'Download FAILED',
                                                              __addon__.getAddonInfo('icon')))


def on_download_failed(download):
    logger.debug('------------------------------------------------------------')
    logger.notice('Download has failed: ' + repr(download))
    logger.debug('------------------------------------------------------------')
