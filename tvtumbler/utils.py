'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import sys
import requests
import platform
import uuid
from . import logger, jsonrpc

__addon__ = sys.modules["__main__"].__addon__
__addonname__ = __addon__.getAddonInfo('name')
__addonversion__ = __addon__.getAddonInfo('version')

INSTANCE_ID = str(uuid.uuid1())
_user_agent = None


def get_url_as_json(url):
    headers = {'User-Agent': get_user_agent()}
    r = requests.get(url, headers=headers)
    if r.status_code != requests.codes.ok:
        logger.notice('Bad status from %s, status code %d' % (url, r.status_code))
        return None

    try:
        json_obj = r.json()
    except Exception, e:
        logger.warning(u"%s failed to parse json response: %s" % (url, str(e)))
        return None

    return json_obj


def get_user_agent():
    global _user_agent
    if not _user_agent:
        xv = jsonrpc.application_get_properties()
        # logger.debug(repr(xv))
        _user_agent = ('%s/%s (%s; %s; %s) %s/%d.%dr%s-%s' % (__addonname__, __addonversion__,
                                                              platform.system(), platform.release(), INSTANCE_ID,
                                                              xv['name'],
                                                              xv['version']['major'], xv['version']['minor'],
                                                              xv['version']['revision'], xv['version']['tag']
                                                              ))
    return _user_agent
