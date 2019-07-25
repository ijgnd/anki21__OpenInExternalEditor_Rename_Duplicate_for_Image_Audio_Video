# License AGPLv3, see main

import re
import os
import shutil

from aqt.utils import showInfo
from aqt.qt import *

from .helper import (
    process_path,
    get_unused_new_name,
    replace_sound_in_editor_and_reload,
    replace_img_in_editor_and_reload
)


def new_unused_name_auto_increment(mediafolder, base, ext):
    n = re.findall(r'''_(\d*)$''', base)
    if len(n) > 0:
        n_at_end = n[0]
        if n_at_end:
            l = len(n_at_end)
            newbase = base[:-l] + str(int(n_at_end)+1)
    else:
        newbase = base + "_1"
    newfilename = newbase + ext
    if os.path.exists(os.path.join(mediafolder, newfilename)):
        newfilename = new_unused_name_auto_increment(mediafolder, newbase, ext)
    return newfilename


def new_duplicate_name(editor, fname, extended):
    mediafolder, fileabspath, base, ext = process_path(fname)
    newfilename = False
    if extended:
        newfilename = get_unused_new_name(mediafolder, base + "_", ext)
    if not extended:
        newfilename = new_unused_name_auto_increment(mediafolder, base, ext)
    return newfilename


def _duplicate(editor, fname, type, field):
    mediafolder, fileabspath, base, ext = process_path(fname)
    if os.path.isfile(fileabspath):
        extended = editor.mw.app.queryKeyboardModifiers() & Qt.ShiftModifier
        newfilename = new_duplicate_name(editor, fname, extended)
        if newfilename:
            newabs = os.path.join(mediafolder, newfilename)
            shutil.copy(fileabspath, newabs)
            # update fields
            if type == "sound":
                searchstring = '[sound:' + fname + ']'
                replacestring = searchstring + '[sound:' + newfilename + ']'
                replace_sound_in_editor_and_reload(
                    editor, searchstring, replacestring, field)
            elif type == "image":
                replace_img_in_editor_and_reload(
                    editor, fname, newfilename, "duplicate", field)
