'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

from .showrss import ShowRSSFeeder
from .ezrss import EZRSSFeeder

_active_feeders = None


def get_active_feeders():
    '''
    Get a list of all currently active (enabled) feeders.

    @return: ([BaseFeeder]) Returns a list of BaseFeeder objects, ordered by preference (highest first)
    '''
    global _active_feeders
    if _active_feeders is None:
        _active_feeders = [EZRSSFeeder(), ShowRSSFeeder()]
    return _active_feeders


def get_latest():
    '''
    Calls get_latest() on all active feeders and concatenates the result

    @return: ([Downloadable]) Returns a list of Downloadable's
    '''
    latest = []
    for f in get_active_feeders():
        latest.extend(f.get_latest())

    return latest
