#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2011, Fredy Wijaya
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

import wx, sys, threading, os, subprocess, cStringIO, youtubedl
from wx.lib.mixins.listctrl import TextEditMixin
 
class YouTubeDownloaderGuiFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "YouTubeDownloaderGUI", size=(800, 500))
        icon_file = "youtube-icon.png"
        icon = wx.Icon(icon_file, wx.BITMAP_TYPE_PNG)
        self.SetIcon(icon)
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        self._create_top_components(panel, vbox)
        self._create_center_components(panel, vbox)
        self._create_bottom_components(panel, vbox)
        panel.SetSizer(vbox)
        self.youtubedownloader = YouTubeDownloader()
       
    def _create_top_components(self, panel, vbox):
        fgs = wx.FlexGridSizer(2, 3, 10, 10)
        
        url_lbl = wx.StaticText(panel, label="URL")
        self.url_txt = wx.TextCtrl(panel)
        self.add_btn = wx.Button(panel, label="Add")
        self.add_btn.Bind(wx.EVT_BUTTON, self._add_url)
        
        dest_lbl = wx.StaticText(panel, label="Destination")
        self.dest_txt = wx.TextCtrl(panel)
        self.dest_txt.Disable()
        self.dest_txt.SetValue(os.path.join(os.path.expanduser("~"),
                                            "Downloads"))
        self.dest_btn = wx.Button(panel, label="Open")
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
        self.convert_to_mp3_chk = wx.CheckBox(panel, label="Convert to MP3",)
        hbox.Add(self.convert_to_mp3_chk, flag=wx.LEFT | wx.RIGHT, border=10)
        vbox.Add(hbox, flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=10)
   
    def _create_center_components(self, panel, vbox):
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.url_list = EditableTextListCtrl(panel, style=wx.LC_REPORT)
        self.url_list.Bind(wx.EVT_LIST_END_LABEL_EDIT, self._edit_item)
        self.url_list.InsertColumn(0, 'File Name')
        self.url_list.InsertColumn(1, 'URL')
        self.url_list.SetColumnWidth(0, 400)
        self.url_list.SetColumnWidth(1, 800)
        hbox.Add(self.url_list, flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
                 proportion=1, border=10)
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        self.up_btn = wx.Button(panel, label="Up")
        self.up_btn.Disable()
        self.up_btn.Bind(wx.EVT_BUTTON, self._move_item_up)
        vbox1.Add(self.up_btn, flag=wx.BOTTOM, border=10)
        self.down_btn = wx.Button(panel, label="Down")
        self.down_btn.Disable()
        self.down_btn.Bind(wx.EVT_BUTTON, self._move_item_down)
        vbox1.Add(self.down_btn, flag=wx.BOTTOM, border=10)
        self.remove_btn = wx.Button(panel, label="Remove")
        self.remove_btn.Disable()
        self.remove_btn.Bind(wx.EVT_BUTTON, self._remove_items)
        vbox1.Add(self.remove_btn, flag=wx.BOTTOM, border=10)
        hbox.Add(vbox1, flag=wx.LEFT | wx.RIGHT, border=10)
       
        vbox.Add(hbox, flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT,
                 proportion=1, border=10)
    
    def _edit_item(self, event):
        if FileNameSanitizer().contains_illegal_chars(event.GetLabel()):
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
        self.download_btn = wx.Button(panel, label="Download")
        self.download_btn.Disable()
        self.download_btn.Bind(wx.EVT_BUTTON, self._download)
        hbox.Add(self.download_btn, flag=wx.LEFT | wx.RIGHT, border=10)
        vbox.Add(hbox, flag=wx.TOP | wx.ALL, border=10)

    def _add_url(self, event):
        if self.url_txt.GetValue() == "":
            wx.MessageDialog(self, message="URL can't be empty", caption="Error",
                             style=wx.ICON_ERROR | wx.CENTRE).ShowModal()
            return
        if (not self.url_txt.GetValue().lower().startswith("http://") and
            not self.url_txt.GetValue().lower().startswith("https://")):
            wx.MessageDialog(self, message="Invalid URL", caption="Error",
                             style=wx.ICON_ERROR | wx.CENTRE).ShowModal()
            return
        index = self.url_list.InsertStringItem(sys.maxint, "")
        self.url_list.SetStringItem(index, 0, "Default")
        self.url_list.SetStringItem(index, 1, self.url_txt.GetValue())
        VideoTitleRetrieverThread(self, self.url_txt.GetValue(), 
                                  index).start()
        self.download_btn.Disable()
        self.remove_btn.Enable()
        self.up_btn.Enable()
        self.down_btn.Enable()
        
    def _open_file(self, event):
        dlg = wx.DirDialog(self, style=wx.OPEN)
        if dlg.ShowModal() ==  wx.ID_OK:
            self.dest_txt.SetValue(dlg.GetPath())
    
    def _download(self, event):
        if not os.path.exists(self.dest_txt.GetValue()):
            os.makedirs(self.dest_txt.GetValue())
        urls = []
        for i in range(0, self.url_list.GetItemCount()):
            urls.append((self.url_list.GetItem(i, 0).GetText(),
                         self.url_list.GetItem(i, 1).GetText()))
        self.youtubedownloader.download(urls, self.dest_txt.GetValue(),
                                        self.convert_to_mp3_chk.GetValue())
    
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
    def __init__(self):
        self.illegal_chars = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|"]
        
    def contains_illegal_chars(self, filename):
        for char in self.illegal_chars:
            if char in filename: return True
        return False
        
    def sanitize(self, filename):
        sanitized_filename = filename
        for char in self.illegal_chars:
            sanitized_filename = sanitized_filename.replace(char, "")
        return sanitized_filename

mutex = threading.Lock()

class VideoTitleRetrieverThread(threading.Thread):
    def __init__(self, frame, url, index):
        threading.Thread.__init__(self)
        self.frame = frame
        self.url = url
        self.index = index
        self.filename_sanitizer = FileNameSanitizer()
    
    def run(self):
        fd = youtubedl.FileDownloader({'forcetitle':True,
                                       'simulate':True,
                                       'outtmpl':u'%(id)s.%(ext)s',
                                       'quiet':True})
        yie = youtubedl.YoutubeIE(fd)
        yie.initialize()
        filename = self._capture(yie.extract, self.url).strip() + ".flv"
        filename = self.filename_sanitizer.sanitize(filename)
        self.frame.url_list.SetStringItem(self.index, 0, filename)
        self.frame.download_btn.Enable()
    
    def _capture(self, func, *args, **kwargs):
        mutex.acquire()
        tmpstdout = sys.stdout
        sys.stdout = cStringIO.StringIO()
        try:
            func(*args, **kwargs)
        finally:
            value = sys.stdout.getvalue()
            sys.stdout = tmpstdout
        mutex.release()
        return value

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

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = YouTubeDownloaderGuiFrame()
    frame.Centre()
    frame.Show(True)
    app.MainLoop()
