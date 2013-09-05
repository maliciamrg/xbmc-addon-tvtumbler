'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
from .. import logger

_enabled_downloaders = None


def get_enabled_downloaders():
    '''Get a list of enabled downloaders - higher priority ones first.

    @return: A list of downloaders - higher priority ones first.
    @rtype: [BaseDownloader]
    '''
    global _enabled_downloaders
    if _enabled_downloaders is None:
        from . import rasterbar
        from . import trpc
        _all_downloaders = [rasterbar.LibtorrentDownloader, trpc.TRPCDownloader]
        enabled_downloaders = [ad.get_instance() for ad in _all_downloaders if ad.is_available() and ad.is_enabled()]
    return enabled_downloaders


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
    logger.debug('------------------------------------------------------------')
    logger.notice('Download has downloaded: ' + repr(download))
    logger.debug('------------------------------------------------------------')


def on_download_failed(download):
    logger.debug('------------------------------------------------------------')
    logger.notice('Download has failed: ' + repr(download))
    logger.debug('------------------------------------------------------------')
