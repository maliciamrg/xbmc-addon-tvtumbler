'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import requests
from . import logger
import xbmc
import sys

import elementtree.ElementTree as etree

# see http://wiki.xbmc.org/index.php?title=Add-on:Common_plugin_cache
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

TVDB_API_KEY = 'FCC2D40061D489B4'
__addon__     = sys.modules[ "__main__" ].__addon__
__addonname__ = __addon__.getAddonInfo('name')

cache = StorageServer.StorageServer(__addonname__ + __name__, 6)  # 6 hrs


# def _get_xml_text(node):
#     text = ""
#     for child_node in node.childNodes:
#         if child_node.nodeType in (Node.CDATA_SECTION_NODE, Node.TEXT_NODE):
#             text += child_node.data
#     return text.strip()


def tvdb_series_lookup(tvdb_id):
    '''
    Look up a series from thetvdb.

    @param tvdb_id: (int)
    @return: On failure, returns None, on Success returns a dict with the keys
        'id', 'SeriesName', 'IMDB_ID', 'SeriesID', 'zap2it_id', and 'Network'.
    '''
    # if we have a cached result, we use that.
    url = 'http://thetvdb.com/api/%s/series/%s/en.xml' % (TVDB_API_KEY,
                                                          str(tvdb_id))
    data = cache.get(url)
    if not data:
        logger.debug('getting url %s' % url)
        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            # logger.debug('encoding is ' + r.encoding)
            logger.debug('raw data returned is ' + repr(r.text))
            data = r.text.encode('ascii', 'ignore')
            cache.set(url, data)
        else:
            logger.notice('No data returned from tvdb for %s, ' +
                          'status code %d' % (tvdb_id, r.status_code))
            return None

    logger.debug(u'got data: %s' % data)
    parsedXML = etree.fromstring(data)
    series = parsedXML.find('Series')
    if not series:
        logger.debug('No series tag for %s' % tvdb_id)
        return None

#     def _text_from_node(nodeName):
#         n = series.getElementsByTagName(nodeName)
#         if n.length == 0:
#             return None
#         else:
#             return _get_xml_text(n[0])

    # http://thetvdb.com/api/FCC2D40061D489B4/series/256204/en.xml
    return {
        'id'        : tvdb_id,
        'SeriesName': series.findtext('SeriesName'),
        'IMDB_ID'   : series.findtext('IMDB_ID'),
        'SeriesID'  : series.findtext('SeriesID'),
        'zap2it_id' : series.findtext('zap2id_id'),
        'Network'   : series.findtext('Network'),
    }

