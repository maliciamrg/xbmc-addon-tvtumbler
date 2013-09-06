'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import os
import xbmcvfs

from .. import logger, utils, jsonrpc, events

_enabled_downloaders = None


def on_settings_changed():
    logger.debug('Settings changed, resetting enabled downloaders')
    global _enabled_downloaders
    _enabled_downloaders = None

events.add_event_listener(events.SETTINGS_CHANGED, on_settings_changed)


def get_enabled_downloaders():
    '''Get a list of enabled downloaders - higher priority ones first.

    @return: A list of downloaders - higher priority ones first.
    @rtype: [BaseDownloader]
    '''
    global _enabled_downloaders
    if _enabled_downloaders is None:
        from . import rasterbar, trpc
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
            return d.download(downloadable)

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

    @param download: The download that has downloaded.
    @type download: base.Download
    '''
    logger.debug('------------------------------------------------------------')
    logger.notice('Download has downloaded: ' + repr(download))
    logger.debug('------------------------------------------------------------')
    tv_show_dir = download.downloadable.tvshow.get_path()
    all_tvdb_episodes = [ep.tvdb_episodes for ep in download.episodes]  # this is a list of tuples (season, episode)
    all_tvdb_seasons = list(set([x[0] for x in all_tvdb_episodes]))
    feeder = download.downloadable.feeder
    name_parser = feeder.get_nameparser()
    any_files_copied = False
    for f in download.get_files():
        if utils.is_video_file(f):
            if not xbmcvfs.exists(f):
                logger.notice(u'Downloader reported that file "%s" is downloaded, but it cannot '
                              u'be found.' % (f,))
                continue

            np = name_parser(os.path.basename(f), has_ext=True,
                             numbering_system=feeder.get_numbering())
            if np.is_known:
                # if the filename is parsable, then we use the season for the first
                # episode in the filename (using tvdb numbering)
                season = np.episodes[0].tvdb_episodes[0][0]

                # quick safety check: if the filename triggered any of our 'bad' regexes,
                # then we had better ignore it.
                if np.is_bad:
                    logger.notice(u'Downloaded file "%s" triggered a bad regex, not copying.' % (f,))
                    continue

            elif len(all_tvdb_seasons) == 1:
                # file name is not parsable, but there is only one
                # season in this download, so we know where to put it.
                season = all_tvdb_seasons[0]
            else:
                logger.notice(u'Problem dealing with file %s after download. '
                              u'The download spans seasons, and we cannot work out the season '
                              u'for this particular file, so we don\'t know where to put it.' % (f,))
                continue

            dest_dir = os.path.join(tv_show_dir, 'Season %d' % (season,))
            xbmcvfs.mkdirs(dest_dir)
            dest_file = os.path.join(dest_dir, os.path.basename(f))
            logger.info(u'Copying file from "%s" to "%s".' % (f, dest_file))
            if xbmcvfs.copy(f, dest_file):
                logger.info('Success!')
                any_files_copied = True
            else:
                logger.info('Failed!')
    if any_files_copied:
        jsonrpc.videolibrary_scan(tv_show_dir)

def on_download_failed(download):
    logger.debug('------------------------------------------------------------')
    logger.notice('Download has failed: ' + repr(download))
    logger.debug('------------------------------------------------------------')
