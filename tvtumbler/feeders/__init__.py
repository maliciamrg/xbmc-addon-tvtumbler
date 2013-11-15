'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

from .. import events, logger

_enabled_feeders = None


def on_settings_changed():
    logger.debug('Settings changed, resetting enabled feeders')
    global _enabled_feeders
    _enabled_feeders = None

events.add_event_listener(events.SETTINGS_CHANGED, on_settings_changed)


def get_enabled_feeders():
    '''
    Get a list of all currently enabled feeders.

    @return: ([BaseFeeder]) Returns a list of BaseFeeder objects, ordered by preference (highest first)
    '''
    global _enabled_feeders
    if _enabled_feeders is None:
        from . import ezrss, publichd
        _all_feeders = [ezrss.EZRSSFeeder, publichd.PublicHDFeeder]
        _enabled_feeders = [f.get_instance() for f in _all_feeders if f.is_available() and f.is_enabled()]
    return _enabled_feeders


def get_latest():
    '''
    Calls get_latest() on all active feeders and concatenates the result

    @return: ([Downloadable]) Returns a list of Downloadable's
    '''
    latest = []
    for f in get_enabled_feeders():
        latest.extend(f.get_latest())
    return latest


def get_updates():
    '''
    Calls get_latest() on all active feeders *that are due an update* and concatenates the result

    @return: ([Downloadable]) Returns a list of Downloadable's
    '''
    latest = []
    for f in get_enabled_feeders():
        if f.is_update_due():
            latest.extend(f.get_latest())
    return latest
