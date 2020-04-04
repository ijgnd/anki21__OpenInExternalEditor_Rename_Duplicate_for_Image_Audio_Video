# License AGPLv3, see main

import os
from shutil import which
import subprocess

from anki.utils import isMac, isWin, isLin, noBundledLibs
from aqt.qt import *
from aqt.utils import showInfo

from .helper import process_path, osascript_to_args

def myOpenFolder(path):
    """mod of aqt.utils openFolder"""
    if isWin:
        # subprocess.Popen(["explorer", ])  # original version, doesn't work in 2019-12
        subprocess.Popen('explorer /select, {}'.format("file://"+path))
    elif isMac:
        with noBundledLibs():
            script = """
            tell application \"Finder\"
                activate
                select POSIX file \"{}\"
            end tell
            """.format(path)
            subprocess.Popen(osascript_to_args(script))
    elif isLin:
        if which("dolphin") is not None:
            # BUT in 2019-05 (in KDE) openFolder doesn't work for me in the prebuilt/compiled version
            # from Ankiweb. If I use runanki with my local PyQt it works
            subprocess.Popen(["dolphin", "--select", "file://"+path])
            # subprocess.Popen(["dolphin","--select",path])  #also works
        elif which("nautilus") is not None:
            # caja 1.20 doesn't have "--select"
            subprocess.Popen(["nautilus", "--select", "file://"+path])
        else:
            filename = os.path.dirname(path)
            showInfo("The file manager will show your media folder. The name of the file you "
                     "clicked is:\n\n{}".format(filename))
            dirname = os.path.dirname(path)
            QDesktopServices.openUrl(QUrl("file://" + dirname)


def show_in_filemanager(editor, filename):
    mediafolder, fileabspath, base, ext = process_path(filename)
    # openFolder(fileabspath)
    # BUT doens't help: mp3 files are opened in the default audio player etc.
    # BUT in 2019-05 (in KDE) openFolder doesn't work for me in the prebuilt/compiled version
    # from Ankiweb. If I use runanki with my local PyQt it works
    # I tried in 2.1.12 without add-ons and in Preferences -> Backups I clicked
    # on "Open Backup Folder". I got this:
    # qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
    # This application failed to start because no Qt platform plugin could be initialized.
    # Reinstalling the application may fix this problem.
    # Available platform plugins are: eglfs, linuxfb, minimal, minimalegl, offscreen, vnc,
    # wayland-egl, wayland, wayland-xcomposite-egl, wayland-xcomposite-glx, xcb.
    # /usr/bin/xdg-open: line 613:  8817 Aborted  (core dumped) kde-open${KDE_SESSION_VERSION} "$1"
    myOpenFolder(fileabspath)
