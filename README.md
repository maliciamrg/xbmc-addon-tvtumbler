xbmc-addon-tvtumbler
====================

This is a TV show downloader for XMBC.
It watches torrent RSS feeds for new episodes in 'followed' TV shows in your library, and downloads any that you don't
have.

WARNING: This is **pre-alpha** code, use at your own risk, and do not expect it to work completely yet!

Requirements:
-------------

- [XBMC 13.0 (Gotham)](http://mirrors.xbmc.org/snapshots/) or [XBMC 12.2 (Frodo)](http://xbmc.org/download/).
- A working XBMC TV library (i.e. in Video -> Library -> TV Shows you have some entries listed) which uses thetvdb.com
numbering system (most will by default).
- [Transmission Bittorrent Client](http://www.transmissionbt.com/) Running somewhere on the network.  The default
download dir must be accessible to XBMC.

(Other bittorrent clients are in the pipeline, but Transmission is the easiest to get started with)

Setup:
------

- Install this addon to your XBMC (get the [latest zip from here](http://repo.tvtumbler.com/service.tvtumbler/)).
- Open the addon settings (System -> Settings -> Addons -> Enabled Addons -> Services -> TvTumbler -> Configure)
- In **Feeders**: enable at least one (or several if you prefer).
- In **Libtorrent**: leave this disabled, it doesn't work for now.
- In **Transmission**: enable it, and set all required settings.  The `Download Dir` is where XMBC will look for 
completed downloads. (Preferably this should be a public share with password-less write access, or a directory on the
xbmc machine itself)

When first run, none of the shows in your library will be 'followed'.  You'll need to follow at least a few:

- Open the addon through 'Programs' or 'Video Addons'.  After a few seconds you should get a list of shows in your 
library.
- Select a show to toggle the 'follow' status.  Right click (context menu) will allow you to change the desired quality.

Notes:
------

- This is pre-alpha code.  Don't expect it to work without problems.
- Libtorrent is broken for now, don't enable it (unless you're a dev and want to fix it).
- Air-by-date shows are currently skipped when searching feeds.  (they are searched in backlog though)
- Anime shows don't really work at all.  Sorry.  (if anyone who's into Anime is interested in fixing this, then please
  contact me).
- Frodo users will be prompted to restart XBMC after any addon update.  This is a bug with Frodo: http://trac.xbmc.org/ticket/14609
  (it's a bug with Gotham too, but we can work around it there by restarting the service)
- The ShowRSS feeder is dead weight for now: use the other two.  (this will probably be removed in the near future, as 
  it doesn't really add anything).
- Users running XBMC on a Pi (raspbmc, openelec etc) - please expect some issues.  The Pi has several small quirks that
  break XBMC in unexpected ways. (You can alleviate some of these by enabling 'safe file copy' in advanced settings)


