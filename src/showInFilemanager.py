# License AGPLv3, see edit_insert_rename_duplicate.py

from .config import anki_point_version, gc

import os
from shutil import which
import subprocess

if anki_point_version <= 49:
    from anki.utils import (
        isLin,
        isMac,
        isWin,
        noBundledLibs
    )
else:
    from anki.utils import no_bundled_libs as noBundledLibs
    from anki.utils import is_lin as isLin
    from anki.utils import is_mac as isMac
    from anki.utils import is_win as isWin


from aqt.qt import (
    QDesktopServices,
    QUrl,
)
from aqt.utils import (
    showInfo,
)


from .helper import (
    check_if_executable_exists,
    env_adjust,
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
        us = check_if_executable_exists(us[0])
        if not us:
            return
        if us:
            us.append("file://" + path)
            subprocess.Popen(us, env=env_adjust())
        else:
            select_supported = ["dolphin", "nautilus"]   # caja 1.24 doesn't have "--select"
            for fm in select_supported:
                if which(fm) is not None:
                    subprocess.Popen([fm, "--select", "file://" + path], env=env_adjust())
            else:
                showInfo( "The file manager will show your media folder. The name of the file you "
                         f"clicked is:\n\n{os.path.dirname(path)}")
                with noBundledLibs():
                    QDesktopServices.openUrl(QUrl("file://" + os.path.dirname(path)))
