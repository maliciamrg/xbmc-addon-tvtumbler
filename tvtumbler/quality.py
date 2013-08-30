'''
This file is part of TvTumbler.

Lots of this is robbed from the 'Quality' class in sickbeard.

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import os
import re

SDTV = 1  # 1
SDDVD = 1 << 1  # 2
HDTV = 1 << 2  # 4
RAWHDTV = 1 << 3  # 8  -- 720p/1080i mpeg2 (trollhd releases)
FULLHDTV = 1 << 4  # 16 -- 1080p HDTV (QCF releases)
HDWEBDL = 1 << 5  # 32
FULLHDWEBDL = 1 << 6  # 64 -- 1080p web-dl
HDBLURAY = 1 << 7  # 128
FULLHDBLURAY = 1 << 8  # 256

# put these bits at the other end of the spectrum, far enough out that they shouldn't interfere
UNKNOWN_QUALITY = 1 << 15  # 32768

SD_COMP = SDTV | SDDVD
HD_COMP = HDTV | RAWHDTV | FULLHDTV | HDWEBDL | FULLHDWEBDL | HDBLURAY | FULLHDBLURAY  # HD720p + HD1080p
HD720P_COMP = HDTV | HDWEBDL | HDBLURAY
HD1080P_COMP = FULLHDTV | FULLHDWEBDL | FULLHDBLURAY
ANY = SDTV | SDDVD | HDTV | RAWHDTV | FULLHDTV | HDWEBDL | FULLHDWEBDL | HDBLURAY | FULLHDBLURAY | UNKNOWN_QUALITY

quality_strings = {
                   # basic qualities
                   UNKNOWN_QUALITY: "Unknown",
                   SDTV: "SD TV",
                   SDDVD: "SD DVD",
                   HDTV: "HD TV",
                   RAWHDTV: "RawHD TV",
                   FULLHDTV: "1080p HD TV",
                   HDWEBDL: "720p WEB-DL",
                   FULLHDWEBDL: "1080p WEB-DL",
                   HDBLURAY: "720p BluRay",
                   FULLHDBLURAY: "1080p BluRay",

                   # composites
                   SD_COMP: 'SD',
                   HD_COMP: 'HD',
                   HD720P_COMP: 'HD720p',
                   HD1080P_COMP: 'HD1080p',
                   ANY: 'ANY'
                   }


def quality_from_name(filename, guess_from_extension=True):
    '''
    Determine the quality from a filename.

    @param filename: (str) Full path, or just a filename.
    @param guess_from_extension: (bool)
    @return: (int) One of SDTV, SDDVD, HDTV, ... UNKNOWN_QUALITY.
    '''
    filename = os.path.basename(filename)

    # if we have our exact text then assume we put it there
    for x in sorted(quality_strings, reverse=True):
        if x == UNKNOWN_QUALITY:
            continue

        regex = '\W' + quality_strings[x].replace(' ', '\W') + '\W'
        regex_match = re.search(regex, filename, re.I)
        if regex_match:
            return x

    check_name = lambda alist, func: func([re.search(x, filename, re.I) for x in alist])

    if check_name(["(pdtv|hdtv|dsr|tvrip|webrip).(xvid|x264)"], all) and not check_name(["(720|1080)[pi]"], all):
        return SDTV
    elif check_name(["(dvdrip|bdrip)(.ws)?.(xvid|divx|x264)"], any) and not check_name(["(720|1080)[pi]"], all):
        return SDDVD
    elif check_name(["720p", "hdtv", "x264"], all) or check_name(["hr.ws.pdtv.x264"], any) and not check_name(["(1080)[pi]"], all):
        return HDTV
    elif check_name(["720p|1080i", "hdtv", "mpeg-?2"], all):
        return RAWHDTV
    elif check_name(["1080p", "hdtv", "x264"], all):
        return FULLHDTV
    elif check_name(["720p", "web.dl|webrip"], all) or check_name(["720p", "itunes", "h.?264"], all):
        return HDWEBDL
    elif check_name(["1080p", "web.dl|webrip"], all) or check_name(["1080p", "itunes", "h.?264"], all):
        return FULLHDWEBDL
    elif check_name(["720p", "bluray|hddvd", "x264"], all):
        return HDBLURAY
    elif check_name(["1080p", "bluray|hddvd", "x264"], all):
        return FULLHDBLURAY

    if guess_from_extension:
        return _guess_quality_from_extension(filename)

    return UNKNOWN_QUALITY


def _guess_quality_from_extension(filename):
    if filename.lower().endswith((".avi", ".mp4")):
        return SDTV
    elif filename.lower().endswith(".mkv"):
        return HDTV
    elif filename.lower().endswith(".ts"):
        return RAWHDTV
    else:
        return UNKNOWN_QUALITY
