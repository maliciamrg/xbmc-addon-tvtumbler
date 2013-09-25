'''
This file is part of TvTumbler.

Created on Sep 25, 2013

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''
import xbmc
import xbmcgui
from .actions import *
from .. import logger
from ..comms.client import service_api, ServerNotRunningException

class TvTumblerWindowXML(xbmcgui.WindowXML):

    def check_service_ok(self):
        '''
        Check if the service is running and the version is ok.
        Will prompt to restart/start if needed.

        Returns false if everything isn't ok 
        @rtype: bool
        '''
        client_version = service_api.get_client_version()
        try:
            server_version = service_api.get_version()
        except ServerNotRunningException, e:
            logger.info(str(e))
            server_version = 'NOTRUNNING'
        logger.debug('Client Version: %s, Server Version: %s' % (client_version, server_version))
        if client_version == server_version:
            return True

        # some intervention needed to fix things ...

        if server_version == 'NOTRUNNING':
            # Server is not running.  Ask them do they want to start it
            dlg = xbmcgui.Dialog()
            if dlg.yesno(heading='TvTumbler', line1='Backend Service is Stopped',
                         line2='Would you like to start it now?', nolabel='Cancel', yeslabel='Start Service'):
                if not service_api.start_service():
                    dlg.ok('TvTumbler', 'Service failed to start.', 'Please restart XMBC.')
                    return False
            else:
                # they clicked no, we just have to exit the gui here
                return False
        elif client_version != server_version:
            dlg = xbmcgui.Dialog()
            if dlg.yesno(heading='TvTumbler', line1='Backend Service has been updated, restart needed.',
                         line2='Would you like to restart the service now?', nolabel='No', yeslabel='Restart Service'):
                if not service_api.restart_service():
                    dlg.ok('TvTumbler', 'Service failed to restart.', 'Please restart XMBC.')
                    return False

        count = 0
        while count < 30:
            try:
                server_version = service_api.get_version()
                logger.debug('Got new server version: ' + str(server_version))
                return True
            except ServerNotRunningException, e:
                xbmc.sleep(1000)
                count = count + 1

        dlg.ok('TvTumbler', 'Service failed to (re)start.', 'Please restart XMBC.')
        return False
