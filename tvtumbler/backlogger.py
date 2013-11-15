'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import datetime
import sys
import time

import dns.resolver
import dns.exception
import xbmc

from . import logger, epdb, quality, links, downloaders, log


__addon__ = sys.modules["__main__"].__addon__


# The number of days after a missed episode airs before we start looking for it in backlog
BACKLOGGER_START_DAYS_AGO = 1  # i.e. yesterday

# The number of days after a missed episode airs before we give up looking for it in backlog
# BACKLOGGER_END_DAYS_AGO = 8

# @todo: get this from a srv lookup in time
base_domain = 'tvdns.mooo.com'


def run():

    logger.debug('backlogger - run')

    if not __addon__.getSetting('recent_backlogger_enable') == 'true':
        logger.debug('backlogger is disabled.  Skipping')
        return

    backlogger_end_days_ago = BACKLOGGER_START_DAYS_AGO + int(__addon__.getSetting('recent_backlogger_daysback'))

    from . import main, numbering

    if xbmc.abortRequested or main.shutdownRequested:
        return

    # we use utc date so that australian users won't start searching backlog before the episode airs!
    today_utc = datetime.datetime.utcnow().date()
    for days_ago in range(BACKLOGGER_START_DAYS_AGO, backlogger_end_days_ago):
        the_date = today_utc - datetime.timedelta(days=days_ago)

        all_eps = epdb.get_episodes_on_date(the_date, True)
        for ep in all_eps:
            # anything that we want won't have an episodeid
            if not ep.episodeid and not downloaders.is_downloading(ep) and not log.was_downloaded(ep):
                # check explicitly for the 'ANY' quality, because we want to pass that to the
                # query (rather than a specific quality)
                if quality.ANY == ep.tvshow.wanted_quality:
                    qual = ''
                    recvd_quality = quality.UNKNOWN_QUALITY
                elif ep.is_wanted_in_quality(quality.SDTV):
                    qual = 's.'
                    recvd_quality = quality.SDTV
                elif ep.is_wanted_in_quality(quality.HDTV):
                    qual = 'h.'
                    recvd_quality = quality.HDTV
                else:
                    # not wanted, or too specific for current backlog mechanisms
                    continue

                queries = set()
                for tvdb_ep in ep.tvdb_episodes:
                    qname = '%s%s.%s.%s.t.%s' % (qual, str(tvdb_ep[1]), str(tvdb_ep[0]),
                                                 str(ep.tvshow.tvdb_id), base_domain)

                    queries.add(qname)

                infohash = None
                for q in queries:
                    try:
                        logger.debug('search for ' + q)
                        answers = dns.resolver.query(q, 'TXT')
                        s = answers[0].strings[0]
                        if len(s) == 40:  # here hashes should always be 40 chars
                            infohash = s
                            break

                    except (dns.resolver.NoAnswer, IndexError, dns.resolver.NXDOMAIN,
                            dns.exception.Timeout):
                        logger.debug('no answer for ' + q)
                        pass

                if infohash:
                    magnet = 'magnet:?xt=urn:btih:' + infohash

                    torrent_name = ep.fake_local_filename(use_numbering=numbering.TVDB_NUMBERING)

                    torrent = links.Torrent(urls=[magnet],
                                            episodes=[ep],
                                            name=torrent_name,
                                            quality=recvd_quality)

                    downloaders.download(torrent)


    logger.debug('backlogger is finished')
