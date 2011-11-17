from distutils.core import setup
import py2exe
import shutil, os, sys
from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED

ver = "0.2.3"
youtube_dl_gui = "youtube-dl-gui"
youtube_dl_gui_linux = youtube_dl_gui + "-" + ver + "-linux"
youtube_dl_gui_win32 = youtube_dl_gui + "-" + ver + "-win32"

def make_win32_package(package_dir):
    shutil.copy("ffmpeg.exe", "dist")
    shutil.copy("ffprobe.exe", "dist")
    shutil.copy("youtube-icon.png", "dist")
    shutil.copy("youtube-icon.ico", "dist")
    shutil.move("dist", package_dir)
    create_zip(package_dir)
    shutil.rmtree(package_dir)
    shutil.rmtree("build")

def make_linux_package(package_dir):
    if not os.path.exists(package_dir):
        os.mkdir(package_dir)
    shutil.copy("youtube-dl-gui.py", package_dir)
    shutil.copy("youtubedl.py", package_dir)
    shutil.copy("youtube-icon.png", package_dir)
    shutil.copy("youtube-icon.ico", package_dir)
    create_zip(package_dir)
    shutil.rmtree(package_dir)

def error(msg):
    print "Error:", msg
    sys.exit(1)
    
def create_zip(path):
    if not os.path.isdir(path): error(path + " is not a directory")
    zip_filename = os.path.basename(path) + ".zip"
    with closing(ZipFile(zip_filename, "w", ZIP_DEFLATED)) as z:
        for root, dirs, files in os.walk(path):
            for f in files:
                z.write(os.path.join(root, f))

if os.path.exists(youtube_dl_gui_win32):
    shutil.rmtree(youtube_dl_gui_win32)
if os.path.exists(youtube_dl_gui_linux):
    shutil.rmtree(youtube_dl_gui_linux)
    
setup(console=["youtubedl.py"])
setup(name=youtube_dl_gui,
      version=ver,
      author='Fredy Wijaya',
      windows=[{"script":"youtube-dl-gui.py"}],
      options={"py2exe":{"includes":["sip"]}})

make_win32_package(youtube_dl_gui_win32)
make_linux_package(youtube_dl_gui_linux)