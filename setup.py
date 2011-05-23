from distutils.core import setup
import py2exe
import shutil, os

setup(console=["youtubedl.py"])
setup(name='youtube-dl-gui',
      version='0.1',
      author='Fredy Wijaya',
      windows=[{"script":"youtube-dl-gui.py"}],
      options={"py2exe":{"includes":["sip"]}})
shutil.copy("ffmpeg.exe", "dist")
shutil.copy("ffprobe.exe", "dist")
shutil.copy("youtube-icon.png", "dist")
shutil.move("dist", "youtube-dl-gui-0.1-win32")

if not os.path.exists("youtube-dl-gui-0.1-linux"):
    os.mkdir("youtube-dl-gui-0.1-linux")
shutil.copy("youtube-dl-gui.py", "youtube-dl-gui-0.1-linux")
shutil.copy("youtubedl.py", "youtube-dl-gui-0.1-linux")
shutil.copy("youtube-icon.png", "youtube-dl-gui-0.1-linux")