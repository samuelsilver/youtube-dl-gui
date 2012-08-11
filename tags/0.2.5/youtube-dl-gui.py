#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2011-2012, Fredy Wijaya
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the Lesser GNU General Public License as published by
# the Free Software Foundation, either version 3.0 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# Lesser GNU General Public License for more details.
#
# You should have received a copy of the Lesser GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>

import wx, sys, threading, os, subprocess, cStringIO, youtubedl, urllib2, re
from ConfigParser import ConfigParser
from wx.lib.mixins.listctrl import TextEditMixin
from wx.lib.pubsub import setupv1
from wx.lib.pubsub import Publisher

__author__  = u"Fredy Wijaya"
__version__ = u"0.2.5"

UPDATE_URL = u"http://code.google.com/p/youtube-dl-gui/source/browse/trunk/VERSION.txt"
DOWNLOAD_URL = u"http://code.google.com/p/youtube-dl-gui/downloads/list"

mutex = threading.Lock()

class YouTubeDownloaderGUIFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, u"YouTubeDownloaderGUI " + __version__,
                          size=(800, 500))
        self.settings = YouTubeDownloaderGUISettings()
        icon_file = "youtube-icon.ico"
        icon = wx.Icon(icon_file, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        self._create_top_components(panel, vbox)
        self._create_center_components(panel, vbox)
        self._create_bottom_components(panel, vbox)
        panel.SetSizer(vbox)
        self.youtubedownloader = YouTubeDownloader()
        # register all the subscriptions
        Publisher().subscribe(self._get_update, "update")
        Publisher().subscribe(self._get_video_title, "video_title")
       
    def _create_top_components(self, panel, vbox):
        fgs = wx.FlexGridSizer(2, 3, 10, 10)
        
        url_lbl = wx.StaticText(panel, label=u"URL")
        self.url_txt = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.url_txt.Bind(wx.EVT_KEY_DOWN, self._add_url_when_enter_pressed)
        self.add_btn = wx.Button(panel, label=u"Add")
        self.add_btn.Bind(wx.EVT_BUTTON, self._add_url)
        
        dest_lbl = wx.StaticText(panel, label=u"Destination")
        self.dest_txt = wx.TextCtrl(panel)
        self.dest_txt.Disable()
        download_path = self.settings.get(u"Download", u"path")
        if not download_path:
             download_path = os.path.join(os.path.expanduser("~"),
                                          u"Downloads")
             self.settings.set(u"Download", u"path", download_path)
        self.dest_txt.SetValue(download_path)
        self.dest_btn = wx.Button(panel, label=u"Open")
        self.dest_btn.Bind(wx.EVT_BUTTON, self._open_file)
        
        fgs.AddMany([(url_lbl, 0, wx.LEFT | wx.RIGHT, 10),
                     (self.url_txt, 1, wx.EXPAND | wx.LEFT | wx.RIGHT),
                     (self.add_btn, 0, wx.LEFT | wx.RIGHT, 10),
                     (dest_lbl, 0, wx.LEFT | wx.RIGHT, 10),
                     (self.dest_txt, 1, wx.EXPAND | wx.LEFT | wx.RIGHT),
                     (self.dest_btn, 0, wx.LEFT | wx.RIGHT, 10)])
        fgs.AddGrowableCol(1, 1)
        vbox.Add(fgs, flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=10)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.convert_to_mp3_chk = wx.CheckBox(panel, label=u"Convert to MP3",)
        hbox.Add(self.convert_to_mp3_chk, flag=wx.LEFT | wx.RIGHT, border=10)
        vbox.Add(hbox, flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=10)
   
    def _create_center_components(self, panel, vbox):
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.url_list = EditableTextListCtrl(panel, style=wx.LC_REPORT)
        self.url_list.Bind(wx.EVT_LIST_END_LABEL_EDIT, self._edit_item)
        self.url_list.InsertColumn(0, u"File Name")
        self.url_list.InsertColumn(1, u"URL")
        self.url_list.SetColumnWidth(0, 400)
        self.url_list.SetColumnWidth(1, 800)
        self.url_list.Bind(wx.EVT_KEY_DOWN, self._remove_items_when_del_pressed)
        hbox.Add(self.url_list, flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
                 proportion=1, border=10)
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.up_btn = wx.Button(panel, label=u"Up")
        self.up_btn.Disable()
        self.up_btn.Bind(wx.EVT_BUTTON, self._move_item_up)
        vbox1.Add(self.up_btn, flag=wx.BOTTOM, border=10)
        self.down_btn = wx.Button(panel, label=u"Down")
        self.down_btn.Disable()
        self.down_btn.Bind(wx.EVT_BUTTON, self._move_item_down)
        vbox1.Add(self.down_btn, flag=wx.BOTTOM, border=10)
        self.remove_btn = wx.Button(panel, label=u"Remove")
        self.remove_btn.Disable()
        self.remove_btn.Bind(wx.EVT_BUTTON, self._remove_items)
        vbox1.Add(self.remove_btn, flag=wx.BOTTOM, border=10)
        hbox.Add(vbox1, flag=wx.LEFT | wx.RIGHT, border=10)
       
        vbox.Add(hbox, flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
                 proportion=1, border=10)
    
    def _edit_item(self, event):
        if FileNameSanitizer.contains_illegal_chars(event.GetLabel()):
            event.Veto()
        else: event.Allow()
    
    def _move_item_down(self, event):
        index = self.url_list.GetFirstSelected()
        if index == -1: return
        if self.url_list.GetSelectedItemCount() > 1: return
        # already at the bottom
        if index == self.url_list.GetItemCount()-1: return
        self._swap_items(index+1, index)
    
    def _move_item_up(self, event):
        index = self.url_list.GetFirstSelected()
        if index == -1: return
        if self.url_list.GetSelectedItemCount() > 1: return
        # already at the top
        if index == 0: return
        self._swap_items(index-1, index)
        
    def _swap_items(self, index1, index2):
        filename1 = self.url_list.GetItem(index1, 0).GetText()
        url1 = self.url_list.GetItem(index1, 1).GetText()
        filename2 = self.url_list.GetItem(index2, 0).GetText()
        url2 = self.url_list.GetItem(index2, 1).GetText()
        
        self.url_list.SetStringItem(index1, 0, filename2)
        self.url_list.SetStringItem(index1, 1, url2)
        self.url_list.SetStringItem(index2, 0, filename1)
        self.url_list.SetStringItem(index2, 1, url1)
        
    def _remove_items_when_del_pressed(self, event):
        if (event.GetKeyCode() == wx.WXK_DELETE):
            self._remove_items(event)
        else: event.Skip()
            
    def _remove_items(self, event):
        indices = []
        index = self.url_list.GetFirstSelected()
        if index == -1: return
        indices.append(index)
        while len(indices) != self.url_list.GetSelectedItemCount():
            index = self.url_list.GetNextSelected(index)
            indices.append(index)
        # it is important to sort in ascending order
        for index in sorted(indices, reverse=True):
            self.url_list.DeleteItem(index)
        if self.url_list.GetItemCount() == 0:
            self.up_btn.Disable()
            self.down_btn.Disable()
            self.remove_btn.Disable()
            self.download_btn.Disable()
    
    def _create_bottom_components(self, panel, vbox):
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.download_btn = wx.Button(panel, label=u"Download")
        self.download_btn.Disable()
        self.download_btn.Bind(wx.EVT_BUTTON, self._download)
        hbox.Add(self.download_btn, flag=wx.LEFT | wx.RIGHT)
        
        self.check_update_btn = wx.Button(panel, label=u"Check for Update")
        self.check_update_btn.Bind(wx.EVT_BUTTON, self._check_for_update)
        hbox.Add(self.check_update_btn, flag=wx.LEFT | wx.RIGHT, border=10)
        
        url_lbl = wx.StaticText(panel, label=u"Created by %s" % __author__)
        hbox.Add(url_lbl, flag=wx.LEFT | wx.CENTER | wx.RIGHT, border=10)
        vbox.Add(hbox, flag=wx.TOP | wx.ALL, border=10)

    def _add_url_when_enter_pressed(self, event):
        if (event.GetKeyCode() == wx.WXK_RETURN):
            self._add_url(event)
        else: event.Skip()
        
    def _add_url(self, event):
        if self.url_txt.GetValue() == u"":
            wx.MessageDialog(self, message=u"URL can't be empty", caption=u"Error",
                             style=wx.ICON_ERROR | wx.CENTRE).ShowModal()
            return
        
        index = self.url_list.InsertStringItem(sys.maxint, u"")
        self.url_list.SetStringItem(index, 0, u"Default")
        self.url_list.SetStringItem(index, 1, self.url_txt.GetValue())
        # check if the URL is playlist URL
        if YouTubeURLChecker.is_playlist(self.url_txt.GetValue()):
            self.url_list.SetStringItem(index, 0, u"*** PLAYLIST ***")
            self.url_list.SetStringItem(index, 1, self.url_txt.GetValue())
            self.download_btn.Enable()
        else:
            VideoTitleRetrieverThread(self.url_txt.GetValue(), index).start()

        self.remove_btn.Enable()
        self.up_btn.Enable()
        self.down_btn.Enable()
        
    def _open_file(self, event):
        dlg = wx.DirDialog(self, style=wx.OPEN)
        if dlg.ShowModal() ==  wx.ID_OK:
            self.settings.set(u"Download", u"path", dlg.GetPath())
            self.dest_txt.SetValue(dlg.GetPath())
    
    def _download(self, event):
        if not os.path.exists(self.dest_txt.GetValue()):
            os.makedirs(self.dest_txt.GetValue())
        urls = []
        for i in range(0, self.url_list.GetItemCount()):
            name = self.url_list.GetItem(i, 0).GetText()
            url = self.url_list.GetItem(i, 1).GetText()
            # for playlist, use the default file name
            if YouTubeURLChecker.is_playlist(url): name = u"%(title)s.%(ext)s"
            urls.append((name, url))
        self.youtubedownloader.download(urls, self.dest_txt.GetValue(),
                                        self.convert_to_mp3_chk.GetValue())
    
    def _check_for_update(self, event):
        YouTubeDownloaderGUIUpdaterThread(__version__).start()
        self.check_update_btn.Disable()
    
    def _get_update(self, msg):
        model = msg.data
        if model.error:
            wx.MessageDialog(frame, message=model.message, 
                             caption=u"Check for Update", 
                             style=wx.ICON_ERROR | wx.CENTRE).ShowModal()
        else:
            wx.MessageDialog(frame, message=model.message, 
                             caption=u"Check for Update", 
                             style=wx.ICON_INFORMATION | wx.CENTRE).ShowModal()
        self.check_update_btn.Enable()
    
    def _get_video_title(self, msg):
        model = msg.data
        if model.error:
            wx.MessageDialog(None, model.message, u"Error", 
                             wx.OK | wx.ICON_ERROR).ShowModal()
            self.url_list.DeleteItem(model.index)
        else:
            self.url_list.SetStringItem(model.index, 0, model.filename)
        self.download_btn.Enable()


class YouTubeDownloaderGUISettings(object):
    def __init__(self):
        self.filename = "settings.ini"
        self.cp = ConfigParser()
        if os.path.exists(self.filename):
            with open(self.filename, "rb") as settings_file:
                self.cp.readfp(settings_file)
    
    def set(self, section, key, value):
        if not self.cp.has_section(section):
            self.cp.add_section(section)
        self.cp.set(section, key, value)
        with open(self.filename, "wb") as settings_file:
            self.cp.write(settings_file)
    
    def get(self, section, key):
        if self.cp.has_option(section, key):
            return self.cp.get(section, key)
        return None
    
    
class EditableTextListCtrl(wx.ListCtrl, TextEditMixin):
    def __init__(self, parent, style=0):
        wx.ListCtrl.__init__(self, parent, style=style)
        TextEditMixin.__init__(self)
        # the edit mode should happen only when the user double clicks
        # on the row, but the TextEditMixin implementation
        # binds both the wx.EVT_LEFT_DOWN and wx.EVT_LEFT_DCLICK
        # for the self.OnLeftDown handler, thus the wx.EVT_LEFT_DOWN
        # needs to be unbound
        self.Unbind(wx.EVT_LEFT_DOWN)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDown)
        
    def OpenEditor(self, col, row):
        if col == 1: return
        else: TextEditMixin.OpenEditor(self, col, row)


class FileNameSanitizer(object):
    ILLEGAL_CHARS = [u"\\", u"/", u":", u"*", u"?", u"\"", u"<", u">", u"|"]
    
    @staticmethod    
    def contains_illegal_chars(filename):
        for char in FileNameSanitizer.ILLEGAL_CHARS:
            if char in filename: return True
        return False
    
    @staticmethod
    def sanitize(filename):
        return youtubedl.sanitize_title(filename)


class VideoTitleRetrieverModel(object):
    def __init__(self, index, filename, error=False, message=u""):
        self.error = error
        self.message = message
        self.index = index
        self.filename = filename


class CustomFileDownloader(youtubedl.FileDownloader):
    """ youtubedl.FileDownloader doesn't store the info_dict returned from
        youtubedl.InfoExtractor. This class subclasses youtubedl.FileDownloader
        to store the info_dict as an instance variable """
    def __init__(self, params):
        youtubedl.FileDownloader.__init__(self, params)
        
    def process_info(self, info_dict):
        self.info_dict = info_dict
        youtubedl.FileDownloader.process_info(self, info_dict)
        
    def clear_info(self):
        self.info_dict = None
        
    
class VideoTitleRetrieverThread(threading.Thread):
    def __init__(self, url, index):
        threading.Thread.__init__(self)
        self.url = url
        self.index = index
    
    def run(self):
        fd = CustomFileDownloader({"simulate": True,
                                   "outtmpl": u"%(title)s.%(ext)s",
                                   "quiet": True})
        yie = youtubedl.YoutubeIE(fd)
        yie.initialize()
        try:
            mutex.acquire()
            yie.extract(self.url)
            filename = u'%(title)s.%(ext)s' % fd.info_dict
            # make sure to clear the info afterwards
            fd.clear_info()
            model = VideoTitleRetrieverModel(self.index, filename)
            wx.CallAfter(Publisher().sendMessage, "video_title", model)
        except youtubedl.DownloadError as e:
            msg = u"Unable to download the video. Is the URL correct?"
            model = VideoTitleRetrieverModel(self.index, "", True, msg)
            wx.CallAfter(Publisher().sendMessage, "video_title", model)
        finally:    
            mutex.release()


class YouTubeDownloaderThread(threading.Thread):
    def __init__(self, directory, filename, url, to_mp3):
        threading.Thread.__init__(self)
        self.directory = directory
        self.filename = filename
        self.url = url
        self.to_mp3 = to_mp3
        
    def run(self):
        path = os.path.join(self.directory, self.filename)
        cmdlinebuilder = None
        if sys.platform.lower().startswith("win"):
            cmdlinebuilder = WindowsCmdLineBuilder(path, self.url, self.to_mp3)
        else: cmdlinebuilder = LinuxCmdLineBuilder(path, self.url,
                                                   self.to_mp3)
        subprocess.call(cmdlinebuilder.build())

            
class CommandLineBuilder(object):
    def __init__(self, path, url, to_mp3):
        self.cmdlist = ["-o", path]
        if to_mp3:
            self.cmdlist.append("--extract-audio")
            self.cmdlist.append("--audio-format=mp3")
        self.cmdlist.append(url)
        
    def build(self):
        programlist = self._getprogram()
        program = ""
        if len(programlist) == 1: program = programlist[0]
        else: program = programlist[1]
        if not os.path.exists(program):
            programlist = ["python", "youtubedl.py"]
        newcmdlist = []
        newcmdlist.extend(self._getshell())
        newcmdlist.extend(programlist)
        newcmdlist.extend(self.cmdlist)
        return newcmdlist
        
    def _getshell(self): pass
    def _getprogram(self): pass

   
class WindowsCmdLineBuilder(CommandLineBuilder):
    def _getprogram(self):
        return ["youtubedl.exe"]
    
    def _getshell(self):
        return ["cmd", "/C", "start"]


class LinuxCmdLineBuilder(CommandLineBuilder):
    def _getprogram(self):
        return ["python", "youtubedl.py"]
        
    def _getshell(self):
        return ["xterm", "-e"]


class YouTubeDownloader(object):
    def download(self, url_list, dest_dir, to_mp3=False):
        for filename, url in url_list:
            thread = YouTubeDownloaderThread(dest_dir, filename, url, to_mp3)
            thread.start()


class YouTubeDownloaderGUIUpdater(object):
    def __init__(self, current_version):
        self.current_version = current_version
        
    def check_for_update(self):
        f = urllib2.urlopen(UPDATE_URL)
        reply = f.read()
        m = re.search(u"<td class=\"source\">(.*)<br></td>", reply)
        if not m: return
        latest_version = m.group(1)
        if self._is_latest_version(self.current_version, latest_version):
            return self.current_version
        else: return latest_version
    
    def _is_latest_version(self, current_ver, latest_ver):
        current_vers = current_ver.split(".")
        latest_vers = latest_ver.split(".")
        for i in range(0, len(latest_vers)):
            if i >= len(current_vers): return False
            if int(latest_vers[i]) != int(current_vers[i]): 
                return False
        return True


class YouTubeDownloaderGUIUpdaterModel(object):
    def __init__(self, error, message):
        self.error = error
        self.message = message


class YouTubeDownloaderGUIUpdaterThread(threading.Thread):
    def __init__(self, current_version):
        threading.Thread.__init__(self)
        self.current_version = current_version
        self.updater = YouTubeDownloaderGUIUpdater(current_version)
        
    def run(self):
        try:
            latest_version = self.updater.check_for_update()
            if latest_version == self.current_version:
                msg = (u"You already have the latest version (" + 
                       latest_version + ")")
            else:
                msg = (u"A new version (" + latest_version + 
                       u") is available.\n\nYou can download it from " + 
                       DOWNLOAD_URL)
            model = YouTubeDownloaderGUIUpdaterModel(False, msg)
            wx.CallAfter(Publisher().sendMessage, "update", model)
        except urllib2.HTTPError:
            msg = u"Unable to check for update!"
            model = YouTubeDownloaderGUIUpdaterModel(False, msg)
            wx.CallAfter(Publisher().sendMessage, "update", model)


class YouTubeURLChecker(object):
    @staticmethod
    def is_playlist(url):
        return (True if re.match(youtubedl.YoutubePlaylistIE._VALID_URL, url)
                else False)


if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = YouTubeDownloaderGUIFrame()
    frame.Centre()
    frame.Show(True)
    app.MainLoop()
