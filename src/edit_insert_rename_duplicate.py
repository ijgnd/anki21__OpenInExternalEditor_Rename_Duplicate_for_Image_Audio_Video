"""
Anki Add-on "OpenInExternalEditor,Rename,Duplicate for Image,Audio,Video"

Copyright (c):
- 2019- ijgned
- Ankitects Pty Ltd and contributors
- 2016 mkpoli, Audio Renamer https://ankiweb.net/shared/info/1828964467
- 2016 Stevie Poppe, Remove Missing Audio References https://ankiweb.net/shared/info/1328067109
- 2018 ChrisK91 Edit Images Externally, Updated (Windows) https://ankiweb.net/shared/info/771313609
- 2016-18 glutanimate, Image Occlusion Enhanced https://github.com/glutanimate/image-occlusion-enhanced
- 2016 Dimitry Mikheev, Edit Audio Images https://ankiweb.net/shared/info/1075177705
                                          https://ankiweb.net/shared/info/1040866511
- 2016 anonymous, Edit Images Externally (Mac OSx) https://ankiweb.net/shared/info/1829440730
- 2020 Y. H. Lai (yhlai-code) https://github.com/ijgnd/anki21__OpenInExternalEditor_Rename_Duplicate_for_Image_Audio_Video/pull/2

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

 * rename.apply_to_notes uses code from Audio Renamer which is covered by
 * the following copyright and permission notice:
 *
 * @author: mkpoli
 * https://github.com/mkpoli
 * License WTFPL
"""


import os

from anki.hooks import addHook
from anki.lang import _
from anki.utils import isMac, isWin, isLin
from aqt import mw
from aqt.qt import *
from aqt.editor import Editor
from aqt.utils import tooltip


from .duplicate import _duplicate
from .editExternal import _editExternal, new_and_edit, reviewer_context_edit_img_external
from .helper import has_one_sound, same_filename_in_just_one_editor
from .rename import _rename
from .showInFilemanager import show_in_filemanager


def gc(arg, fail=False):
    conf =  mw.addonManager.getConfig(__name__)
    if conf:
        return conf.get(arg, fail)
    else:
        return fail


##############################################################################
###### Editor Context Menu

# def cme(menu,text,func):
#     a = menu.addAction(_(text))
#     a.triggered.connect(func)


def cmd_filemanager(menu, e, fname, text):
    if isMac:
        fmname = "Finder"
    elif isWin:
        fmname = "Explorer"
    else:
        fmname = "File Manager"
    a = menu.addAction(_("Show this %s in %s" % (text, fmname)))
    a.triggered.connect(lambda _, ed=e, fn=fname: show_in_filemanager(ed, fn))


def helper(editor, func, fname, type):
    field = editor.currentField
    if field:
        editor.saveNow(lambda: func(editor, fname, type, field))
    else:
        editor.saveNow(lambda: func(editor, fname, type, None))


def add_to_context(view, menu):
    # image detection code is from IO
    context_data = view.page().contextMenuData()
    url = context_data.mediaUrl()
    fname = url.fileName()
    fileabspath = os.path.join(mw.col.media.dir(), fname)
    e = view.editor

    if not url.isValid():
        ni = (gc("image_empty_insert_and_edit__show_in_editor_context_menu", False),
            "ni",
            "New Empty Image and Edit")
        fp = (gc("image_diagram_mindmap__freeplane_path", False),
            "fp",
            "Inset New Mindmap and Edit with Freeplane")
        dia = (gc("image_diagram_mindmap__dia_path", False),
            "dia",
            "Insert New Diagram and Edit with Dia")
        draw = (gc("image_diagram_mindmap__draw_path", False),
            "drawio",
            "Insert New Diagram and Edit with Drawio")
        lo = (gc("image_diagram_mindmap__CalcDraw_path", False),
            "lo",
            "Insert New Diagramdand Edit with LibreOffice Draw")
        total = 0
        for f in [ni, fp, dia, draw, lo]:
            if f[0]:
                total += 1
        if total > 1:
            menu_create_edit = menu.addMenu('&create and edit')
            for i in [ni, fp, dia, draw, lo]:
                if i[0]:
                    a = menu_create_edit.addAction(i[2])
                    a.triggered.connect(lambda _, o=i[1], ed=e: new_and_edit(e, o))
        else:
            for i in [ni, fp, dia, draw]:  # only one is True
                if i[0]:
                    a = menu.addAction(i[2])
                    a.triggered.connect(lambda _, o=i[1], ed=e: new_and_edit(e, o))
    if url.isValid() and os.path.isfile(fileabspath):
        if gc("image_edit_externally__show_in_editor_context_menu"):
            a = menu.addAction(_("Edit Image"))
            a.triggered.connect(lambda _, ed=e, fn=fname: helper(ed, _editExternal, fn, "image"))
        if gc("image_rename__show_in_editor_context_menu"):
            if same_filename_in_just_one_editor(fname, "image"):
                a = menu.addAction(_("Rename this Image"))
                a.triggered.connect(lambda _, ed=e, fn=fname: helper(ed, _rename, fn, "image"))
        if gc("image_duplicate__show_in_editor_context_menu"):
            a = menu.addAction(_("Duplicate this Image"))
            a.triggered.connect(lambda _, ed=e, fn=fname: helper(ed, _duplicate, fn, "image"))
        if gc("image__show_context_menu_entry_for__showInExplorerFinderFileManager"):
            cmd_filemanager(menu, e, fname, "image")
    else:
        fname = has_one_sound(view.selectedText())
        if fname:
            fileabspath = os.path.join(mw.col.media.dir(), fname)
            if not os.path.isfile(fileabspath):
                tooltip('Selected File not in media collection. Aborting ...')
                return
            if gc("sound__show_context_menu_entry_for__editExternally"):
                a = menu.addAction(_("Edit this Sound (Audio/Video) externally"))
                a.triggered.connect(lambda _, ed=e, fn=fname: helper(ed, _editExternal, fn, "sound"))
            if gc("sound__show_context_menu_entry_for__rename"):
                if same_filename_in_just_one_editor(fname, "sound"):
                    a = menu.addAction(_("Rename this Sound (Audio/Video)"))
                    a.triggered.connect(lambda _, ed=e, fn=fname: helper(ed, _rename, fn, "sound"))
            if gc("sound__show_context_menu_entry_for__duplicate"):
                a = menu.addAction(_("Duplicate this Sound (Audio/Video)"))
                a.triggered.connect(lambda _, ed=e, fn=fname: helper(ed, _duplicate, fn, "sound"))
            if gc("sound__show_context_menu_entry_for__showInExplorerFinderFileManager"):
                cmd_filemanager(menu, e, fname, "Sound (Audio/Video)")
addHook("EditorWebView.contextMenuEvent", add_to_context)


##############################################################################
###### Image Reviewer Context Menu


def _reviewerContextMenu(view, menu):
    if mw.state != "review":
        return
    # image detection code is from IO
    context_data = view.page().contextMenuData()
    url = context_data.mediaUrl()
    fname = url.fileName()
    path = os.path.join(mw.col.media.dir(), fname)
    if url.isValid() and path:
        a = menu.addAction(_("Edit Image"))
        a.triggered.connect(lambda _, v=view, fn=fname: reviewer_context_edit_img_external(v, fn))
if gc("image_edit_externally__show_in_reviewer_context_menu"):
    addHook('AnkiWebView.contextMenuEvent', _reviewerContextMenu)
