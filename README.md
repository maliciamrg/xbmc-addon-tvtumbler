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
- Restart XMBC.  (this is a bug - will be fixed in time)
- Open the addon settings (System -> Settings -> Addons -> Enabled Addons -> Services -> TvTumbler -> Configure)
- In **Feeders**: enable at least one (or several if you prefer)
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
- Air-by-date shows are currently skipped.
- State of currently running downloads is lost if xbmc is restarted (or the addon is upgraded).
- After the addon is initially installed, you may need to restart xbmc before it will operate. (fixed now?)
- The latest Gotham nightlies (since, I think, [this change](https://github.com/xbmc/xbmc/commit/19212e78eda0716bae7d47ab3223fda3bd84451f#diff-d150a7803ef164a51aa46dcacca5af81))
won't upgrade the addon automatically when a new version is available.  You'll need to upgrade manually (the addon will
show in your available updates, you'll just need to download it and install from zip). 


