# License AGPLv3, see edit_insert_rename_duplicate.py

import os
import re
import subprocess
import shutil
import json
import types
import time
import shlex

from pathlib import Path

from anki.hooks import addHook

from .config import anki_point_version, gc
if anki_point_version <= 49:
    from anki.utils import isMac
else:
    from anki.utils import is_mac as isMac

from aqt import mw
from aqt.editor import Editor
from aqt.utils import getText, showInfo

from .helper import (
    check_if_executable_exists,
    env_adjust,
    process_path,
    time_now_fmt,
)
from .duplicate import new_unused_name_auto_increment


def some_paths():
    global mediafolder
    global addon_path
    mediafolder = os.path.join(mw.pm.profileFolder(), "collection.media")
    addon_path = os.path.dirname(__file__)
addHook("profileLoaded", some_paths)


def open_in_external(fileabspath, external_program, shell=True):
    env = env_adjust()
    if isMac:
        # 2022-09-09 quote the external_program for spaces in executable path name
        cmd = f"open -a '{external_program}' '{fileabspath}'"
        subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    else:
        # in 2019-12 I have no idea why I used shell=True by default in 2019-05.
        if shell:
            subprocess.Popen(f' "{external_program}" "{fileabspath}" ', shell = True, env=env)
        else:
            subprocess.Popen([external_program, fileabspath], env=env)


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
    for prog_path, prog_ext, _, prog_fname_identifier in ec.values():
        if prog_fname_identifier in base:
            abspath = os.path.join(mediafolder, base + prog_ext)
            return prog_path, abspath
    else:
        all = external_progs_and_their_settings(True)
        abspath = os.path.join(mediafolder, base + ext)
        return all['ni'][0], abspath


def _editExternal(editor, fname, type, field):
    mediafolder, fileabspath, base, ext = process_path(fname)
    # detection of file type with proper library might require
    # external dependencies and/or relicensing. That's quicker.
    if type == "image":
        external_program, fileabspath = executable_and_file_for_image(base, ext)
        external_program = check_if_executable_exists(external_program)
        if not external_program:
            return
        if gc("image_edit_externally__block_Anki_during_edit") and not isMac:
            # note: a more recent alternative to check_output is subprocess.run
            subprocess.check_output([external_program, fileabspath])
            # editor.saveTags()  # broken in 2.1.50 - shouldn't be needed 
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
            # handle the paths on the macOS side differently
            if isMac:
                # if the user has forgotten to add fully-qualified path, 
                # assume it is in /Applications
                if not external_program.__contains__('/Applications'):
                    if not external_program.__contains__('.app'):
                        ep_ = f'{external_program}.app'
                        ep_ = f'/Applications/{ep_}'
                        # does the external program exist in system-wide /Applications
                        if not os.path.exists(ep_):
                            # check if it exists in the ~/Applications dir
                            ep_ = f'~/{ep_}'
                            if os.path.exists(ep_):
                                external_program = ep_
                        else:
                            # the external program exists in /Applications
                            external_program = ep_
            open_in_external(fileabspath, external_program)


    Path(mediafolder).touch()


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


def new_name_with_user_query(prog_ext, prog_fname_identifier, prefill=""):
    if prefill:
        text = 'Filename already exists. Try again with a different name.'
    else:
        text = 'Name of the new file: '
        prefill = time_now_fmt()
    name, r = getText(text, default=prefill)
    if not r:
        return None, None, None, None
    sourcename = "_" + prog_fname_identifier + name + prog_ext
    sourcepath = os.path.join(mediafolder, sourcename)
    imagename = "_" + prog_fname_identifier + name + ".png"
    imagepath = os.path.join(mediafolder, imagename)
    for f in [sourcepath, imagepath]:
        if os.path.exists(f):
            return new_name_with_user_query(prog_ext, prog_fname_identifier, prefill=name)
    return sourcename, sourcepath, imagename, imagepath


def editDiaMMExternal(editor, field, prog, template, sourcepath):
    template_full_path = os.path.join(addon_path, "user_files", template)
    shutil.copy(template_full_path, sourcepath)
    copying = True
    size2 = -1
    while copying:
        size = os.path.getsize(sourcepath)
        if size == size2:
            break
        else:
            size2 = os.path.getsize(sourcepath)
            time.sleep(0.1)
    if not isMac:
        subprocess.check_output([prog, sourcepath])
        editor.saveTags()
        editor.web.page().profile().clearHttpCache()
        editor.loadNote(focusTo=field)
    else:
        # in 2019-06 freeplane needs False if openend with freeplane.sh
        open_in_external(sourcepath, prog, False)

    Path(mediafolder).touch()


def new_and_edit(editor, arg):
    if arg == "ni":
        # separate function: historic reasons, also no difference between data and image
        new_and_edit_image(editor)
        return
    prog_path, prog_ext, prog_template, prog_fname_identifier = external_progs_and_their_settings()[arg]
    _, sourcepath, imagename, _ = new_name_with_user_query(prog_ext, prog_fname_identifier)
    if not sourcepath:
        return
    newimg = """<img src="%s">""" % imagename
    editor.web.eval("document.execCommand('inserthtml', false, %s);"
                % json.dumps(newimg))
    editor.saveNow(lambda: editDiaMMExternal(editor, editor.currentField, prog_path, prog_template, sourcepath), keepFocus=True)


def reviewer_context_edit_img_external(view, fname):
    mediafolder, fileabspath, _, _ = process_path(fname)
    external_program = gc('image_edit_externally__program')
    if gc("image_edit_externally__block_Anki_during_edit") and not isMac:
        subprocess.check_output([external_program, fname])
        # Reload image by adding a query parameter at the back
        mw.reviewer.web.eval("""
$('img').each(function(){
    var src = $(this).attr('src');
    src = src.replace(/token=(\d+)&/, '')
    src = src.replace(/\?token=(\d+)/, '')
    src += (src.match(/\?/) ? '&' : '?') + 'token=%d';
    $(this).attr('src', src);
});
        """ % int(time.time()))
    else:
        open_in_external(fileabspath, external_program)

    Path(mediafolder).touch()
