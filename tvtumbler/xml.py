'''
This file is part of TvTumbler.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import re
import xmltodict
from . import logger


def xml_to_dict(xml):
    '''
    Convert an xml string to a dict.

    @param xml: (str) raw xml string.
    @param encoding: (str)
    @return: (dict)
    '''
    return xmltodict.parse(xml, xml_attribs=True)
