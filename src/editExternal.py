# License AGPLv3, see main

import os
import re
import subprocess
import shutil
import json
import types
import time

from anki.hooks import addHook
from anki.utils import isMac, isWin, isLin
from aqt import mw
from aqt.editor import Editor
from aqt.utils import getText, showInfo

from .helper import process_path, time_now_fmt
from .duplicate import new_unused_name_auto_increment
from .config import gc


def some_paths():
    global mediafolder
    global addon_path
    mediafolder = os.path.join(mw.pm.profileFolder(), "collection.media")
    addon_path = os.path.dirname(__file__)
addHook("profileLoaded", some_paths)


def open_in_external(fileabspath, external_program, shell=True):
    if isMac:
        open_command = "open "
        if external_program:
            open_command += '-a %s ' % external_program
        fileabspath = re.sub(" ", "\ ", fileabspath)
        os.system(open_command + fileabspath)
    else:
        # in 2019-12 I have no idea why I used shell=True by default in 2019-05. 
        if shell:
            # subprocess.Popen([external_program, fileabspath], shell=True)
            subprocess.Popen("\"" + external_program+"\"" + " \"" + fileabspath + "\" ", shell = True)
        else:
            # in linux freeplane.sh needs this
            subprocess.Popen([external_program, fileabspath])


def external_progs_and_their_settings(all=True):
    ec = {
        "fp": [gc("image_diagram_mindmap__freeplane_path"),
            ".mm",
            gc("image_diagram_mindmap__freeplane_template"),
            "_fp___",
            ],
        "dia": [gc("image_diagram_mindmap__dia_path"),
            ".dia",
            gc("image_diagram_mindmap__dia_template"),
            "_dia___",
            ],
        "drawio": [gc("image_diagram_mindmap__drawio_path"),
            ".drawio",
            gc("image_diagram_mindmap__drawio_template"),
            "_drawio___",
            ],   
        "lo": [gc("image_diagram_mindmap__CalcDraw_path"),
            ".odg",
            gc("image_diagram_mindmap__CalcDraw_template"),
            "_LODraw___",
            ], 
    }
    if not all:
        return ec
    else:
        ec["ni"] = [gc("image_edit_externally__program"),
            ".png",
            False,
            ]
        return ec


def executable_and_file_for_image(base, ext):
    ec = external_progs_and_their_settings(all=False)
    for p in ec.values():
        if p[3] in base:
            abspath = os.path.join(mediafolder, base + p[1])
            return p[0], abspath
    else:
        all = external_progs_and_their_settings(True)
        abspath = os.path.join(mediafolder, base + ext)
        return all['ni'][0], abspath


def _editExternal(editor, fname, type, field):
    mediafolder, fileabspath, base, ext = process_path(fname)
    # detection of file type with proper library might require
    # external dependencies and/or relicesing. That's quicker.
    if type == "image":
        external_program, fileabspath = executable_and_file_for_image(base, ext)
        if gc("image_edit_externally__block_Anki_during_edit") and not isMac:
            subprocess.check_output([external_program, fileabspath])
            editor.saveTags()
            editor.web.page().profile().clearHttpCache()
            # editor.outerLayout.itemAt(0).widget().setParent(None)
            # editor.outerLayout.itemAt(0).widget().setParent(None)
            # editor.setupWeb()
            # editor.setupTags()
            editor.loadNote(focusTo=field)
        else:
            open_in_external(fileabspath, external_program)
    elif type == "sound":
        if ext.lower()[1:] in gc("sound__extensions_audio"):   # ext has leading "."
            external_program = gc("sound__external_program_audio")
        else:
            external_program = gc("sound__external_program_video")
        if external_program:
            open_in_external(fileabspath, external_program)


def new_and_edit_image(editor):
    template = gc("image_empty_insert_and_edit__file_from_user_files")
    if template:
        template_full_path = os.path.join(addon_path, "user_files", template)
        new_full_path = new_unused_name_auto_increment(mediafolder, time_now_fmt(), ".png")
        newname = os.path.basename(new_full_path)
        if os.path.exists(template_full_path):
            shutil.copy(template_full_path, new_full_path)
        else:
            showInfo("""Error in Add-on "Edit Externally": Template File does not exist.""")
            return
        newimg = """<img src="%s">""" % newname
        editor.web.eval("document.execCommand('inserthtml', false, %s);"
                    % json.dumps(newimg))
        editor.saveNow(lambda:
            _editExternal(editor, newname, "image", editor.currentField))


def new_name_with_user_query(ec, arg, prefill=""):
    if prefill:
        text = 'Filename already exists. Try again with a different name.'
    else:
        text = 'Name of the new file: '
        prefill = time_now_fmt()
    name, r = getText(text, default=prefill)
    if not r:
        return None, None, None, None
    sourcename = "_" + ec[arg][3] + name + ec[arg][1]
    sourcepath = os.path.join(mediafolder, sourcename)
    imagename = "_" + ec[arg][3] + name + ".png"
    imagepath = os.path.join(mediafolder, imagename)
    for f in [sourcepath, imagepath]:
        if os.path.exists(f):
            return new_name_with_user_query(ec, arg, prefill=name)
    return sourcename, sourcepath, imagename, imagepath


def _editDiaMMExternal(editor, field, prog, template, f):
    pass


def editDiaMMExternal(editor, field, prog, template, f):
    #_editDiaMMExternal(editor, field, prog, template, f)
    template_full_path = os.path.join(addon_path, "user_files", template)
    shutil.copy(template_full_path, f.sourcepath)
    copying = True
    size2 = -1
    while copying:
        size = os.path.getsize(f.sourcepath)
        if size == size2:
            break
        else:
            size2 = os.path.getsize(f.sourcepath)
            time.sleep(0.1)
    if not isMac:
        subprocess.check_output([prog, f.sourcepath])
        editor.saveTags()
        editor.web.page().profile().clearHttpCache()
        editor.loadNote(focusTo=field)
    else:
        # in 2019-06 freeplane needs False if openend with freeplane.sh
        open_in_external(f.sourcepath, prog, False)
        

def new_and_edit(editor, arg):
    if arg == "ni":
        # separate function: historic reasons, also no difference between data and image
        new_and_edit_image(editor)
        return
    ec = external_progs_and_their_settings()
    f = types.SimpleNamespace()
    f.sourcename, f.sourcepath, f.imagename, f.imagepath = new_name_with_user_query(ec, arg)
    if not f.sourcepath:
        return
    newimg = """<img src="%s">""" % f.imagename
    editor.web.eval("document.execCommand('inserthtml', false, %s);"
                % json.dumps(newimg))
    editor.saveNow(lambda: editDiaMMExternal(editor, editor.currentField, ec[arg][0], ec[arg][2], f), keepFocus=True)


def reviewer_context_edit_img_external(view, fname):
    mediafolder, fileabspath, base, ext = process_path(fname)
    external_program = gc('image_edit_externally__program')
    # mw.reviewer.web.eval("document.activeElement.blur();")  #?
    if gc("image_edit_externally__block_Anki_during_edit") and not isMac:
        subprocess.check_output([external_program, fname])
        # the similar function for the editor works but not here
        # view.page().profile().clearHttpCache()
        mw.reset(guiOnly=True)  # ?
    else:
        open_in_external(fileabspath, external_program)
