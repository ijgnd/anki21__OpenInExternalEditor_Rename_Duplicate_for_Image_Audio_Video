# License AGPLv3, see main

import os
from shutil import which
import subprocess

from anki.utils import (
    isLin,
    isMac,
    isWin,
    noBundledLibs,
)
from aqt.qt import (
    QDesktopServices,
    QUrl,
)
from aqt.utils import (
    showInfo,
)

from .config import gc
from .helper import (
    osascript_to_args,
    process_path,
)


def show_in_filemanager(filename):
    """mod of aqt.utils openFolder"""
    _, path, _, _ = process_path(filename)
    if isWin:
        subprocess.Popen(f'explorer /select, "file://{path}" ')
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
        us = gc("File Manager in Linux and its args")
        if us:
            us.append("file://" + path)
            with noBundledLibs():
                subprocess.Popen(us)
        else:
            select_supported = ["dolphin", "nautilus"]   # caja 1.24 doesn't have "--select"
            for fm in select_supported:
                if which(fm) is not None:
                    with noBundledLibs():
                        subprocess.Popen([fm, "--select", "file://" + path])
            else:
                showInfo( "The file manager will show your media folder. The name of the file you "
                         f"clicked is:\n\n{os.path.dirname(path)}")
                with noBundledLibs():
                    QDesktopServices.openUrl(QUrl("file://" + os.path.dirname(path)))
