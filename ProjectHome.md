# This project is no longer maintained. For Windows users, you can go to https://github.com/fredyw/win-youtube-dl to get a better tool. For Linux users, just use the command line :) #

A front-end GUI of the popular [youtube-dl.py](http://rg3.github.com/youtube-dl/) Python script. This tool allows downloading multiple videos at the same time and convert them into mp3.

Theoretically, it should run on all platforms, but it is only tested on Windows and Linux.

On Linux, the ffmpeg, ffprobe, and wxPython need to be installed separately.
On Debian derived distros:
```
sudo apt-get install ffmpeg ffprobe python-wxgtk2.8 python-wxtools wx2.8-i18n libwxgtk2.8-dev libgtk2.0-dev libavcodec-extra-5
```
On Windows, those softwares are included in the zip file.

Special thanks to [youtube-dl.py](http://rg3.github.com/youtube-dl/) authors for creating such a wonderful script :)