'''
This file is part of TvTumbler.

Created on Sep 26, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import xml.etree.ElementTree as etree
import requests  # @UnresolvedImport
from . import logger, fastcache


def tvrage_showinfo(tvrage_id, allow_remote_fetch=True):
    '''
    Look up a series from tvrage.
    '''
    if tvrage_id is None:
        return None
    if _real_tvrage_showinfo.is_cached(tvrage_id) or allow_remote_fetch:
        return _real_tvrage_showinfo(tvrage_id)
    return None


@fastcache.func_cache(max_age_secs=60 * 60 * 24)
def _real_tvrage_showinfo(tvrage_id):
    if tvrage_id is None or tvrage_id == '':
        return None
    url = 'http://services.tvrage.com/feeds/showinfo.php?sid=' + str(tvrage_id)
    logger.debug('getting url %s' % url)
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        data = r.text.encode('ascii', 'ignore')
    else:
        logger.notice('No data returned from tvrage for %s, ' +
                      'status code %d' % (str(tvrage_id), r.status_code))
        return None

    logger.debug(u'got data: %s' % data)
    parsedXML = etree.fromstring(data)
    if not parsedXML:
        logger.debug('No valid data for %s' % str(tvrage_id))
        return None

    result = {}

    for c in parsedXML.findall('*'):
        if c.text:
            val = c.text
        else:
            # for now, we simply ignore anything that isn't a text node.  We don't use
            # the extra info (yet)
            continue

        result[c.tag.lower()] = val

    return result
