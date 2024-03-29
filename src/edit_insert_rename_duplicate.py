"""
Anki Add-on "OpenInExternalEditor,Rename,Duplicate for Image,Audio,Video"

Copyright (c):
- 2019- ijgnd
- Ankitects Pty Ltd and contributors
- 2020 BlueGreenMagick
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
"""


import os

from anki.hooks import addHook
from .config import anki_point_version, gc
if anki_point_version <= 49:
    from anki.utils import isMac
    from anki.utils import isWin
else:
    from anki.utils import is_mac as isMac
    from anki.utils import is_win as isWin

from aqt import mw
from aqt.qt import *
from aqt.editor import Editor
from aqt.utils import tooltip


from .config import gc
from .duplicate import _duplicate
from .editExternal import _editExternal, new_and_edit, reviewer_context_edit_img_external
from .helper import has_one_sound, same_filename_in_just_one_editor, clip_copy
from .rename import rename
from .showInFilemanager import show_in_filemanager



##############################################################################
###### Editor Context Menu

# def cme(menu,text,func):
#     a = menu.addAction(text)
#     a.triggered.connect(func)


def cmd_filemanager(menu, fname, text):
    if isMac:
        fmname = "Finder"
    elif isWin:
        fmname = "Explorer"
    else:
        fmname = "File Manager"
    a = menu.addAction(f"{text} - Show in {fmname}")
    a.triggered.connect(lambda _, fn=fname: show_in_filemanager(fn))


def helper(editor, func, fname, type):
    field = editor.currentField
    if field:
        editor.saveNow(lambda: func(editor, fname, type, field))
    else:
        editor.saveNow(lambda: func(editor, fname, type, None))


def add_to_context(view, menu):
    # image detection code is from IO
    if qtmajor == 5:
        context_data = view.page().contextMenuData()
        url = context_data.mediaUrl()
    else:
        # https://doc.qt.io/qt-6/qwebenginecontextmenurequest.html
        context_request = view.lastContextMenuRequest()
        url = context_request.mediaUrl()
    fname = url.fileName()
    fileabspath = os.path.join(mw.col.media.dir(), fname)
    e = view.editor

    if not url.isValid():
        ni = (gc("image_empty_insert_and_edit__show_in_editor_context_menu", False),
              "ni",
              "Image - New Empty Image and Edit"
            )
        fp = (gc("image_diagram_mindmap__freeplane_path", False),
              "fp",
              "Image - Inset New Mindmap and Edit with Freeplane"
            )
        dia = (gc("image_diagram_mindmap__dia_path", False),
               "dia",
               "Image - Insert New Diagram and Edit with Dia"
            )
        draw = (gc("image_diagram_mindmap__draw_path", False),
                "drawio",
                "Image - Insert New Diagram and Edit with Drawio"
            )
        lo = (gc("image_diagram_mindmap__CalcDraw_path", False),
              "lo",
              "Image - Insert New Diagramdand Edit with LibreOffice Draw"
            )
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
            a = menu.addAction("Image - Edit")
            a.triggered.connect(lambda _, ed=e, fn=fname: helper(ed, _editExternal, fn, "image"))
        if gc("image_rename__show_in_editor_context_menu"):
            if same_filename_in_just_one_editor(fname, "image"):
                a = menu.addAction("Image - Rename")
                a.triggered.connect(lambda _, ed=e, fn=fname: helper(ed, rename, fn, "image"))
        if gc("image_duplicate__show_in_editor_context_menu"):
            a = menu.addAction("Image - Duplicate")
            a.triggered.connect(lambda _, ed=e, fn=fname: helper(ed, _duplicate, fn, "image"))
        if gc("image__show_context_menu_entry_for__showInExplorerFinderFileManager"):
            cmd_filemanager(menu, fname, "Image")
        if gc("image__show_context_menu_entry_for__showPathAndPutToClipboard"):
            a = menu.addAction("Image - Copy Path to Clipboard")
            a.triggered.connect(lambda _, fn=fname: clip_copy(fn))
    else:
        fname = has_one_sound(view.selectedText())
        if fname:
            fileabspath = os.path.join(mw.col.media.dir(), fname)
            if not os.path.isfile(fileabspath):
                tooltip('Selected File not in media collection. Aborting ...')
                return
            if gc("sound__show_context_menu_entry_for__editExternally"):
                a = menu.addAction("Sound (Audio/Video) - edit externally")
                a.triggered.connect(lambda _, ed=e, fn=fname: helper(ed, _editExternal, fn, "sound"))
            if gc("sound__show_context_menu_entry_for__rename"):
                if same_filename_in_just_one_editor(fname, "sound"):
                    a = menu.addAction("Sound (Audio/Video) - rename")
                    a.triggered.connect(lambda _, ed=e, fn=fname: helper(ed, rename, fn, "sound"))
            if gc("sound__show_context_menu_entry_for__duplicate"):
                a = menu.addAction("Sound (Audio/Video) - duplicate")
                a.triggered.connect(lambda _, ed=e, fn=fname: helper(ed, _duplicate, fn, "sound"))
            if gc("sound__show_context_menu_entry_for__showInExplorerFinderFileManager"):
                cmd_filemanager(menu, fname, "Sound (Audio/Video)")
            if gc("sound__show_context_menu_entry_for__showPathAndPutToClipboard"):
                a = menu.addAction("Sound - Copy Path to Clipboard")
                a.triggered.connect(lambda _, fn=fname: clip_copy(fn))
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
        a = menu.addAction("Image - edit")
        a.triggered.connect(lambda _, v=view, fn=fname: reviewer_context_edit_img_external(v, fn))
        if gc("image__show_context_menu_entry_for__showInExplorerFinderFileManager"):
            cmd_filemanager(menu, fname, "Image")
        if gc("image__show_context_menu_entry_for__showPathAndPutToClipboard"):
            a = menu.addAction("Image - Copy Path to Clipboard")
            a.triggered.connect(lambda _, fn=fname: clip_copy(fn))
if gc("image_edit_externally__show_in_reviewer_context_menu"):
    addHook('AnkiWebView.contextMenuEvent', _reviewerContextMenu)
