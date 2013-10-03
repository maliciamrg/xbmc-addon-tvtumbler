'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import datetime
import time
import dns.resolver
import xbmc

from . import logger, epdb, quality, links, downloaders


# The number of days after a missed episode airs before we start looking for it in backlog
BACKLOGGER_START_DAYS_AGO = 1

# The number of days after a missed episode airs before we give up looking for it in backlog
BACKLOGGER_END_DAYS_AGO = 8

# @todo: get this from a srv lookup in time
base_domain = 'tvdns.mooo.com'


def run():

    logger.debug('backlogger - run')

    from . import main

    if xbmc.abortRequested or main.shutdownRequested:
        return

    today = datetime.date.today()
    for days_ago in range(BACKLOGGER_START_DAYS_AGO, BACKLOGGER_END_DAYS_AGO):
        the_date = today - datetime.timedelta(days=days_ago)

        all_eps = epdb.get_episodes_on_date(the_date, True)
        for ep in all_eps:
            # anything that we want won't have an episodeid
            if not ep.episodeid and not downloaders.is_downloading(ep):
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

                    except (dns.resolver.NoAnswer, IndexError, dns.resolver.NXDOMAIN):
                        logger.debug('no answer for ' + q)
                        pass

                if infohash:
                    magnet = 'magnet:?xt=urn:btih:' + infohash

                    torrent = links.Torrent(urls=[magnet],
                                            episodes=[ep],
                                            quality=recvd_quality)

                    downloaders.download(torrent)


    logger.debug('backlogger is finished')
