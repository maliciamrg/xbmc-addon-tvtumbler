xbmc-addon-tvtumbler
====================

This is a TV show downloader for XMBC.
It watches torrent RSS feeds for new episodes in all TV shows in your library, and downloads any that you don't have
to your video library automatically.

WARNING: This is **pre-alpha** code, use at your own risk, and do not expect it to work completely yet!

Requirements:
-------------

- [XBMC 13.0 (Gotham)](http://mirrors.xbmc.org/snapshots/) Possibly working on Frodo also, but not tested yet.
- A working XBMC TV library (i.e. in Video -> Library -> TV Shows you have some entries listed) which uses thetvdb.com
numbering system (most will by default).
- [Transmission Bittorrent Client](http://www.transmissionbt.com/) Running somewhere on the network.  The default
download dir must be accessible to XBMC.

(Other bittorrent clients are in the pipeline, but Transmission is the easiest to get started with)

Setup:
-------------

- Install this addon to your XBMC.
- Open the addon settings (System -> Settings -> Addons -> Enabled Addons -> Services -> TvTumbler -> Configure)
- In **Feeders**: enable at least one (or several if you prefer)
- In **Libtorrent**: leave this disabled, it doesn't work for now.
- In **Transmission**: enable it, and set all required settings.  The `Download Dir` is where XMBC will look for completed downloads.

That's it.  The rest is completely automatic.
