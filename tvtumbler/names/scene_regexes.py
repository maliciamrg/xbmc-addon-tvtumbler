'''
This file is part of TvTumbler.

Mostly robbed from sickbeard

@author: Dermot Buckley
@copyright: Copyright (c) 2013, Dermot Buckley
@license: GPL
@contact: info@tvtumbler.com
'''

import re
from .. import logger


def get_regexes():
    '''
    Get a list of compiled regexes.

    @return: list of tuples, (regex_name, compiled_regex)
    '''
    global _compiled_regexes, _ep_regexes
    if _compiled_regexes:
        return _compiled_regexes

    for (cur_pattern_name, cur_pattern) in _ep_regexes:
        try:
            cur_regex = re.compile(cur_pattern, re.VERBOSE | re.IGNORECASE)
        except re.error, errormsg:
            logger.warning(u"WARNING: Invalid episode_pattern, %s. %s" % (errormsg, cur_pattern))
        else:
            _compiled_regexes.append((cur_pattern_name, cur_regex))

    return _compiled_regexes


_compiled_regexes = []

_ep_regexes = [
              ('standard_repeat',
               # Show.Name.S01E02.S01E03.Source.Quality.Etc-Group
               # Show Name - S01E02 - S01E03 - S01E04 - Ep Name
               '''
               ^(?P<series_name>.+?)[. _-]+                # Show_Name and separator
               s(?P<season_num>\d+)[. _-]*                 # S01 and optional separator
               e(?P<ep_num>\d+)                            # E02 and separator
               ([. _-]+s(?P=season_num)[. _-]*             # S01 and optional separator
               e(?P<extra_ep_num>\d+))+                    # E03/etc and separator
               [. _-]*((?P<extra_info>.+?)                 # Source_Quality_Etc-
               ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
               -(?P<release_group>[^- ]+))?)?$              # Group
               '''),

              ('fov_repeat',
               # Show.Name.1x02.1x03.Source.Quality.Etc-Group
               # Show Name - 1x02 - 1x03 - 1x04 - Ep Name
               '''
               ^(?P<series_name>.+?)[. _-]+                # Show_Name and separator
               (?P<season_num>\d+)x                        # 1x
               (?P<ep_num>\d+)                             # 02 and separator
               ([. _-]+(?P=season_num)x                    # 1x
               (?P<extra_ep_num>\d+))+                     # 03/etc and separator
               [. _-]*((?P<extra_info>.+?)                 # Source_Quality_Etc-
               ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
               -(?P<release_group>[^- ]+))?)?$              # Group
               '''),

              ('site_at_start',
               # Several sites doing this now, putting their url at the start for credit
               # (generally just in the torrent name, but also, sometimes in the dir and/or filenames)
               # This is the 'standard' regex, with allowance for this at the beginning.

               # [www.Cpasbien.me] 666.Park.Avenue.S01E13.Vostfr.HDTV.XviD-iTOMa
               # [ www.Torrenting.com ] - American.Idol.S12E35.480p.HDTV.x264-mSD
               # [ www.Torrenting.com ] - Game.of.Thrones.S03E06.HDTV.XviD-AFG
               # [ www.Torrenting.com ] - Men.at.Work.S02E06.HDTV.XviD-AFG
               # [kat.ph]666.park.avenue.s01e12.vostfr.hdtv.xvid.itoma
               '''
               ^(\[.+\][ -]*)                              # likely a web address, surrounded by [ and ]
               ((?P<series_name>.+?)[. _-]+)?              # Show_Name and separator
               s(?P<season_num>\d+)[. _-]*                 # S01 and optional separator
               e(?P<ep_num>\d+)                            # E02 and separator
               (([. _-]*e|-)                               # linking e/- char
               (?P<extra_ep_num>(?!(1080|720)[pi])\d+))*   # additional E03/etc
               [. _-]*((?P<extra_info>.+?)                 # Source_Quality_Etc-
               ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
               -(?P<release_group>[^- ]+))?)?$             # Group
               '''),

              ('standard',
               # Show.Name.S01E02.Source.Quality.Etc-Group
               # Show Name - S01E02 - My Ep Name
               # Show.Name.S01.E03.My.Ep.Name
               # Show.Name.S01E02E03.Source.Quality.Etc-Group
               # Show Name - S01E02-03 - My Ep Name
               # Show.Name.S01.E02.E03
               '''
               ^((?P<series_name>.+?)[. _-]+)?             # Show_Name and separator
               s(?P<season_num>\d+)[. _-]*                 # S01 and optional separator
               e(?P<ep_num>\d+)                            # E02 and separator
               (([. _-]*e|-)                               # linking e/- char
               (?P<extra_ep_num>(?!(1080|720)[pi])\d+))*   # additional E03/etc
               [. _-]*((?P<extra_info>.+?)                 # Source_Quality_Etc-
               ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
               -(?P<release_group>[^- ]+))?)?$              # Group
               '''),

              ('fov',
               # Show_Name.1x02.Source_Quality_Etc-Group
               # Show Name - 1x02 - My Ep Name
               # Show_Name.1x02x03x04.Source_Quality_Etc-Group
               # Show Name - 1x02-03-04 - My Ep Name
               '''
               ^((?P<series_name>.+?)[\[. _-]+)?           # Show_Name and separator
               (?P<season_num>\d+)x                        # 1x
               (?P<ep_num>\d+)                             # 02 and separator
               (([. _-]*x|-)                               # linking x/- char
               (?P<extra_ep_num>
               (?!(1080|720)[pi])(?!(?<=x)264)             # ignore obviously wrong multi-eps
               \d+))*                                      # additional x03/etc
               [\]. _-]*((?P<extra_info>.+?)               # Source_Quality_Etc-
               ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
               -(?P<release_group>[^- ]+))?)?$              # Group
               '''),

              ('scene_date_format',
               # Show.Name.2010.11.23.Source.Quality.Etc-Group
               # Show Name - 2010-11-23 - Ep Name
               '''
               ^((?P<series_name>.+?)[. _-]+)?             # Show_Name and separator
               (?P<air_year>\d{4})[. _-]+                  # 2010 and separator
               (?P<air_month>\d{2})[. _-]+                 # 11 and separator
               (?P<air_day>\d{2})                          # 23 and separator
               [. _-]*((?P<extra_info>.+?)                 # Source_Quality_Etc-
               ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
               -(?P<release_group>[^- ]+))?)?$              # Group
               '''),

              ('stupid',
               # tpz-abc102
               '''
               (?P<release_group>.+?)-\w+?[\. ]?           # tpz-abc
               (?!264)                                     # don't count x264
               (?P<season_num>\d{1,2})                     # 1
               (?P<ep_num>\d{2})$                          # 02
               '''),

              ('verbose',
               # Show Name Season 1 Episode 2 Ep Name
               '''
               ^(?P<series_name>.+?)[. _-]+                # Show Name and separator
               season[. _-]+                               # season and separator
               (?P<season_num>\d+)[. _-]+                  # 1
               episode[. _-]+                              # episode and separator
               (?P<ep_num>\d+)[. _-]+                      # 02 and separator
               (?P<extra_info>.+)$                         # Source_Quality_Etc-
               '''),

#               ('season_only',
#                # Show.Name.S01.Source.Quality.Etc-Group
#                '''
#                ^((?P<series_name>.+?)[. _-]+)?             # Show_Name and separator
#                s(eason[. _-])?                             # S01/Season 01
#                (?P<season_num>\d+)                         # S01 and optional separator
#                [. _-]*((?P<extra_info>.+?)                 # Source_Quality_Etc-
#                ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
#                -(?P<release_group>[^- ]+))?)?$              # Group
#                '''
#                ),

              ('no_season_multi_ep',
               # Show.Name.E02-03
               # Show.Name.E02.2010
               '''
               ^((?P<series_name>.+?)[. _-]+)?             # Show_Name and separator
               (e(p(isode)?)?|part|pt)[. _-]?              # e, ep, episode, or part
               (?P<ep_num>(\d+|[ivx]+))                    # first ep num
               ((([. _-]+(and|&|to)[. _-]+)|-)             # and/&/to joiner
               (?P<extra_ep_num>(?!(1080|720)[pi])(\d+|[ivx]+))[. _-])            # second ep num
               ([. _-]*(?P<extra_info>.+?)                 # Source_Quality_Etc-
               ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
               -(?P<release_group>[^- ]+))?)?$              # Group
               '''
               ),

              ('no_season_general',
               # Show.Name.E23.Test
               # Show.Name.Part.3.Source.Quality.Etc-Group
               # Show.Name.Part.1.and.Part.2.Blah-Group
               '''
               ^((?P<series_name>.+?)[. _-]+)?             # Show_Name and separator
               (e(p(isode)?)?|part|pt)[. _-]?              # e, ep, episode, or part
               (?P<ep_num>(\d+|([ivx]+(?=[. _-]))))                    # first ep num
               ([. _-]+((and|&|to)[. _-]+)?                # and/&/to joiner
               ((e(p(isode)?)?|part|pt)[. _-]?)           # e, ep, episode, or part
               (?P<extra_ep_num>(?!(1080|720)[pi])
               (\d+|([ivx]+(?=[. _-]))))[. _-])*            # second ep num
               ([. _-]*(?P<extra_info>.+?)                 # Source_Quality_Etc-
               ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
               -(?P<release_group>[^- ]+))?)?$              # Group
               '''
               ),

              ('bare',
               # Show.Name.102.Source.Quality.Etc-Group
               '''
               ^(?P<series_name>.+?)[. _-]+                # Show_Name and separator
               (?P<season_num>\d{1,2})                     # 1
               (?P<ep_num>\d{2})                           # 02 and separator
               ([. _-]+(?P<extra_info>(?!\d{3}[. _-]+)[^-]+) # Source_Quality_Etc-
               (-(?P<release_group>.+))?)?$                # Group
               '''),

              ('no_season',
               # Show Name - 01 - Ep Name
               # 01 - Ep Name
               # 01 - Ep Name
               '''
               ^((?P<series_name>.+?)(?:[. _-]{2,}|[. _]))?             # Show_Name and separator
               (?P<ep_num>\d{1,2})                           # 02
               (?:-(?P<extra_ep_num>\d{1,2}))*               # 02
               [. _-]+((?P<extra_info>.+?)                 # Source_Quality_Etc-
               ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
               -(?P<release_group>[^- ]+))?)?$              # Group
               '''
               ),

              ('mvgroup',
               # BBC Lost Kingdoms of South America 3of4 Lands of Gold PDTV x264 AC3mp4-MVGroup
               # BBC.Great.British.Railway.Journeys.Series4.03of25.Stoke-on-Trent.to.Winsford.720p.HDTV.x264.AAC.MVGroup
               '''
               ^(?P<series_name>.+?)[. _-]+                # Show_Name and separator
               ((series|season)(?P<season_num>\d+)[. _-]+)? # Series4
               (?P<ep_num>\d{1,2})of\d{1,2}                # 3of4
               [. _-]+((?P<extra_info>.+?)                 # Source_Quality_Etc-
               ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
               -(?P<release_group>[^- ]+))?)?$
               '''),
              ]

# Anything matching these in either the extra_info or the release_group
# (i.e. the end of the name), will be rejected.
_bad_filters = ["sub(pack|s|bed)", "nlsub(bed|s)?", "swesub(bed)?",
                 "(dir|sample|sub|nfo)fix", "sample", "(dvd)?extras",
                 "dub(bed)?", 'german', 'french', 'core2hd', 'dutch',
                 'swedish']

_compiled_bad_regexes = []


def get_bad_regexes():
    '''
    Get a list of compiled bad regexes.

    @return: list of regexes
    @rtype: [RegexObject]
    '''
    global _compiled_bad_regexes, _bad_filters
    if _compiled_bad_regexes:
        return _compiled_bad_regexes

    for x in _bad_filters:
        cur_pattern = '(^|[\W_])' + x + '($|[\W_])'
        try:
            cur_regex = re.compile(cur_pattern, re.IGNORECASE)
        except re.error, errormsg:
            logger.warning(u"WARNING: Invalid episode_pattern, %s. %s" % (errormsg, cur_pattern))
        else:
            _compiled_bad_regexes.append(cur_regex)

    return _compiled_bad_regexes
