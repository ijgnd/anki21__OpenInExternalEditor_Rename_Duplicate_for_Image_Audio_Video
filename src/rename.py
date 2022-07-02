# License AGPLv3, see edit_insert_rename_duplicate.py

from .config import (
    gc,
    anki_point_version,
)

import re
import os

if anki_point_version >= 45:
    from aqt.operations.note import find_and_replace
if anki_point_version <= 28:
    from anki.find import findReplace

if anki_point_version <= 49:
    from anki.utils import isMac
    from anki.utils import isWin
else:
    from anki.utils import is_mac as isMac
    from anki.utils import is_win as isWin

from aqt import mw
from aqt.utils import tooltip

from .helper import (
    browser_parents,
    process_path,
    get_unused_new_name,
    replace_sound_in_editor_and_reload,
    replace_img_in_editor_and_reload
)


def _replace_all_img_src(parent, orig_name: str, new_name: str):
    "new_name doesn't have whitespace, dollar sign, nor double quote"
    
    orig_name = re.escape(orig_name)
    new_name = new_name

    # Compatibility: 2.1.0+
    n = mw.col.findNotes("<img") if anki_point_version <= 49 else mw.col.find_notes("<img") 

    # src element quoted case
    reg1 = r"""(?P<first><img[^>]* src=)(?:"{name}")|(?:'{name}')(?P<second>[^>]*>)""".format(
        name=orig_name
    )
    # unquoted case
    reg2 = r"""(?P<first><img[^>]* src=){name}(?P<second>(?: [^>]*>)|>)""".format(
        name=orig_name
    )
    img_regs = [reg1]
    if " " not in orig_name:
        img_regs.append(reg2)
    
    if anki_point_version >= 28:
        repl = """${first}"%s"${second}""" % new_name
    else:
        repl = """\\g<first>"%s"\\g<second>""" % new_name

    replaced_cnt = 0
    for reg in img_regs:
        if anki_point_version >= 28:
            op_chg_cnt = mw.col.backend.find_and_replace(
                nids=n,
                search=reg,
                replacement=repl,
                regex=True,
                match_case=False,
                field_name=None,
            )
            if anki_point_version >= 45:
                replaced_cnt += op_chg_cnt.count
            else:
                replaced_cnt = op_chg_cnt
        else:
            replaced_cnt += findReplace(col=mw.col, nids=n, src=reg, dst=repl, regex=True, fold=False)
    return replaced_cnt


def _replace_all_sound_src(orig_name: str, new_name: str):
    "new_name doesn't have whitespace, dollar sign, nor double quote"
    
    old = f"[sound:{orig_name}"
    new = f"[sound:{new_name}"

    # Compatibility: 2.1.0+
    n = mw.col.findNotes("[sound")

    replaced_cnt = 0
    if anki_point_version >= 28:
        op_chg_cnt = mw.col.backend.find_and_replace(
            nids=n,
            search=old,
            replacement=new,
            regex=False,
            match_case=False,
            field_name=None,
        )
        if anki_point_version >= 45:
            replaced_cnt += op_chg_cnt.count
        else:
            replaced_cnt = op_chg_cnt
    else:
        replaced_cnt += findReplace(col=mw.col, nids=n, src=old, dst=new, regex=False, fold=False)
    return replaced_cnt


def backup_changed_filenames(old, new):
    addon_dir_path = os.path.join(os.path.dirname(__file__))
    renamed_file = os.path.join(addon_dir_path, "user_files", "renamed_files.csv")
    with open(renamed_file, "a", encoding="utf-8") as targetfile:
        targetfile.write(f"{old}\t{new}\n")


def notify_user(cnt,  oldname, newfilename):
    s = f'Updated file location/reference in {cnt} note{"s" if cnt > 1 else ""}: <br> from {oldname} to {newfilename}'
    tooltip(s, period=6000)


def rename(editor, fname, type, field):
    mediafolder, fileabspath, base, ext = process_path(fname)
    if os.path.isfile(fileabspath):  # verify
        newfilename = get_unused_new_name(mediafolder, base, ext)
        if newfilename:           
            # reuse from "Image Editor" (307397307 from 2020-07-06)
            # that's more or less its replace_all_img_src
            ep = editor.parentWindow
            br = browser_parents()
            if ep in br:
                ep.model.beginReset()
            if type == "image":
                cnt = _replace_all_img_src(ep, fname, newfilename)
            elif type == "sound":
                cnt = _replace_all_sound_src(fname, newfilename)
            if anki_point_version <= 44:
                mw.requireReset()
            if ep in br:
                ep.model.endReset()
            notify_user(cnt, fname, newfilename)

            if not os.path.isfile(newfilename):
                if isMac:
                    fname_ = os.path.join(mediafolder, fname)
                    newfilename_ = os.path.join(mediafolder, newfilename)
                    os.rename(fname_, newfilename_)
                else:
                    os.rename(fname, newfilename)
            backup_changed_filenames(fname, newfilename)
            
            # update editor
            if type == "sound":
                searchstring = '[sound:' + fname + ']'
                replacestring = '[sound:' + newfilename + ']'
                replace_sound_in_editor_and_reload(
                    editor, searchstring, replacestring, field)
            elif type == "image":
                replace_img_in_editor_and_reload(
                    editor, fname, newfilename, "rename", field)
