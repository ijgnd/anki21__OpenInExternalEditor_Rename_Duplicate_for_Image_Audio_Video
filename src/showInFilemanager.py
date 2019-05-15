# License AGPLv3, see main

import subprocess

from aqt.qt import *
from anki.utils import isMac,isWin,isLin, noBundledLibs

from .helper import process_path


def myOpenFolder(path):
    """mod of aqt.utils openFolder"""
    if isWin:
        subprocess.Popen(["explorer", "file://"+path])
    elif isLin:
        #BUT in 2019-05 (in KDE) openFolder doesn't work for me in the prebuilt/compiled version
        #from Ankiweb. If I use runanki with my local PyQtit works
        subprocess.Popen(["dolphin","--select","file://"+path])
        #subprocess.Popen(["dolphin","--select",path])  #also works
    else:
        with noBundledLibs():
            QDesktopServices.openUrl(QUrl("file://" + path))


def show_in_filemanager(editor, filename):
    mediafolder, fileabspath, base, ext = process_path(filename)
    #openFolder(fileabspath)
    #BUT doens't help: mp3 files are opened in the default audio player etc.
    #BUT in 2019-05 (in KDE) openFolder doesn't work for me in the prebuilt/compiled version
    #from Ankiweb. If I use runanki with my local PyQtit works
    #I tried in 2.1.12 without add-ons and in Preferences -> Backups I clicked
    #on "Open Backup Folder". I got this:
    # qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
    # This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.
    # Available platform plugins are: eglfs, linuxfb, minimal, minimalegl, offscreen, vnc, wayland-egl, wayland, wayland-xcomposite-egl, wayland-xcomposite-glx, xcb.
    # /usr/bin/xdg-open: line 613:  8817 Aborted                 (core dumped) kde-open${KDE_SESSION_VERSION} "$1"
    myOpenFolder(fileabspath) 
