'''
Created on Jun 22, 2013

@author: dermot
'''
from xml.dom.minidom import Node, parseString
import requests
import tvtumbler.logger as logger
import xbmc
import sys

# see http://wiki.xbmc.org/index.php?title=Add-on:Common_plugin_cache
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

TVDB_API_KEY = 'FCC2D40061D489B4'
__addon__     = sys.modules[ "__main__" ].__addon__
__addonname__ = __addon__.getAddonInfo('name')

cache = StorageServer.StorageServer(__addonname__ + __name__, 6)  # 6 hrs


def _get_xml_text(node):
    text = ""
    for child_node in node.childNodes:
        if child_node.nodeType in (Node.CDATA_SECTION_NODE, Node.TEXT_NODE):
            text += child_node.data
    return text.strip()


def tvdb_series_lookup(tvdb_id):
    '''
    Look up a series from thetvdb.

    @param tvdb_id: (int)
    @return: On failure, returns None, on Success returns a dict with the keys
        'id', 'SeriesName', 'IMDB_ID', 'SeriesID', 'zap2it_id', and 'Network'.
    '''
    # if we have a cached result, we use that.
    url = 'http://thetvdb.com/api/%s/series/%s/en.xml' % (TVDB_API_KEY,
                                                          tvdb_id)
    data = cache.get(url)
    if not data:
        logger.debug('getting url %s' % url)
        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            data = r.text
            cache.set(url, r.text)
        else:
            logger.notice('No data returned from tvdb for %s, ' +
                          'status code %d' % (tvdb_id, r.status_code))
            return None

    logger.debug('got data: %s' % data)
    parsedXML = parseString(data)
    series = parsedXML.getElementsByTagName('Series')
    if series.length == 0:
        logger.debug('No series tag for %s' % tvdb_id)
        return None

    series = series[0]  # "there can be only one"

    def _text_from_node(nodeName):
        n = series.getElementsByTagName(nodeName)
        if n.length == 0:
            return None
        else:
            return _get_xml_text(n[0])

    # http://thetvdb.com/api/FCC2D40061D489B4/series/256204/en.xml
    return {
        'id'        : tvdb_id,
        'SeriesName': _text_from_node('SeriesName'),
        'IMDB_ID'   : _text_from_node('IMDB_ID'),
        'SeriesID'  : _text_from_node('SeriesID'),
        'zap2it_id' : _text_from_node('zap2id_id'),
        'Network'   : _text_from_node('Network'),
    }

