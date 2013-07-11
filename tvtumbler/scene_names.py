
import re
import time
import requests
from unidecode import unidecode
import tvtumbler.logger as logger
import tvtumbler.db as db
import tvtumbler.jsonrpc as jsonrpc

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json


SCENE_NAME_REFRESH_INTERVAL_SECS = 60 * 60 * 24
_last_refresh_timestamp = 0


def _get_db():
    try:
        return _get_db.db
    except:
        _get_db.db = db.Connection()
        _get_db.db.action('CREATE TABLE if not exists scene_names ' +
                          '(exception_id INTEGER PRIMARY KEY, ' +
                          'tvdb_id INTEGER KEY, show_name TEXT, ' +
                          'simplified_name TEXT)')
        return _get_db.db


def get_scene_names(tvdb_id):
    """
    Given a tvdb_id, return a list of all the scene names.
    """
    if not tvdb_id:
        return []

    _update_if_needed()

    return [x["show_name"] for x in _get_db().select('SELECT show_name ' +
                                                     'FROM scene_names ' +
                                                     'WHERE tvdb_id = ?',
                                                     [tvdb_id])]


def get_tvdb_id(scene_name):
    """
    Given a show name, return the tvdbid of the show.

    Matches first against shows known to xbmc, then against exceptions.
    Returns the tvdb_id is a match is found, None if no scene name
    match is present.

    @param scene_name: (str|unicode) show name to match
    @return: (int|None) returns an int on success, None on failure.
    """
    # Simplify the name first
    if not isinstance(scene_name, unicode):
        # We assume utf-8
        scene_name = unicode(scene_name, 'utf-8')

    simplified = simplify_show_name(scene_name)

    # start by comparing it to what we have in xbmc
    known_shows = jsonrpc.get_tv_shows(properties=["title"])
    show_matches = [s for s in known_shows if
                    simplify_show_name(s['title']) == simplified]
    if show_matches:
        return int(show_matches[0]['tvdb_id'])

    _update_if_needed()

    # No match in xbmc names?  Continue with the scene exceptions
    myDB = _get_db()

    # try the obvious case first
    result = myDB.select(u'SELECT tvdb_id FROM scene_names ' +
                                   'WHERE simplified_name = ?',
                                   [simplified])
    if result:
        return int(result[0]["tvdb_id"])

    # No match?  We fail
    return None


def simplify_show_name(showName):
    '''

    @param showName: (unicode) Show name to be simplified.  Must be unicode.
    @return: (str)
    '''
    # Replace any unicode chars with their nearest ascii equivalents
    showName = unidecode(showName)
    # strip chars that don't generally appear in scene naming
    bad_chars = u",:()'!?\u2019"
    for x in bad_chars:
        showName = showName.replace(x, "")
    # make it lowercase
    showName = showName.lower()
    # remove all whitespace (yes, even in the middle) - makes searching much
    # more reliable
    showName = re.sub('\s+', '', showName)
    return showName


def _update_scene_names():
    """
    """ 
    url = 'http://show-api.tvtumbler.com/api/exceptions'

    logger.debug(u"Updating scene names from %s" % (url,))
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        url_data = r.text
    else:
        logger.notice('Bad status from %s, ' +
                      'status code %d' % (url, r.status_code))
        return False

    if url_data is None:
        logger.warning(u"_update_scene_names failed. Empty data from url: " + url)
        return False
    else:
        exception_dict = json.loads(url_data)
        myDB = _get_db()
        changed_exceptions = False

        # write all the exceptions we got off the net into the database
        for cur_tvdb_id in exception_dict:

            # get a list of the existing exceptions for this ID
            existing_exceptions = [x["show_name"] for x in 
                                   myDB.select("SELECT * FROM scene_names WHERE tvdb_id = ?", 
                                               [cur_tvdb_id])]

            for cur_exception in exception_dict[cur_tvdb_id]:
                # if this exception isn't already in the DB then add it
                if cur_exception not in existing_exceptions:
                    logger.debug(u'Adding exception %s: %s' % (cur_tvdb_id, cur_exception))
                    myDB.action("INSERT INTO scene_names (tvdb_id, show_name, simplified_name) VALUES (?,?,?)", 
                                [cur_tvdb_id, cur_exception, simplify_show_name(cur_exception)])
                    changed_exceptions = True

            # check for any exceptions which have been deleted
            for cur_exception in existing_exceptions:
                if cur_exception not in exception_dict[cur_tvdb_id]:
                    logger.debug(u'Removing exception %s: %s' % (cur_tvdb_id, cur_exception))
                    myDB.action("DELETE FROM scene_names WHERE tvdb_id = ? AND show_name = ?", [cur_tvdb_id, cur_exception])
                    changed_exceptions = True

        # since this could invalidate the results of the cache we clear it out after updating
        if changed_exceptions:
            logger.info(u"Updated scene exceptions")
            #name_cache.clearCache()
        else:
            logger.debug(u"No scene exceptions update needed")

        return True


def _update_if_needed():
    if time.time() - _last_refresh_timestamp > SCENE_NAME_REFRESH_INTERVAL_SECS:
        _last_refresh_timestamp = time.time()
        _update_scene_names()

