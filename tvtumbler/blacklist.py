'''
This file is part of TvTumbler.

Created on Sep 23, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import time

_blacklisted_urls = dict()


def blacklist_url(url):
    '''
    Add a url to the blacklist.

    @param url: The url to blacklist
    @type url: str
    '''
    global _blacklisted_urls
    _blacklisted_urls[url] = time.time()


def url_is_blacklisted(url, max_age_secs=60 * 60 * 24 * 7):
    '''
    Is a url blacklisted?

    @param url: Url to check
    @type url: str
    @param max_age_secs: Maximum age of blacklist entry in seconds.  Defaults to one week.  If none, there is no
        maximum (i.e. the blacklisting is considered permanent)
    @type max_age_secs: int|None
    @rtype: bool
    '''
    global _blacklisted_urls
    if url in _blacklisted_urls:
        if max_age_secs is None:
            # No max age?  Then an entry is considered permanent
            return True
        age = time.time() - _blacklisted_urls[url]
        return age <= max_age_secs
    return False
