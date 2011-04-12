from distutils.core import setup
import py2exe

setup(console=["youtubedl.py"])
setup(name='youtube-dl-gui',
      version='0.1',
      author='Fredy Wijaya',
      windows=[{"script":"youtube-dl-gui.py"}],
      options={"py2exe":{"includes":["sip"]}})