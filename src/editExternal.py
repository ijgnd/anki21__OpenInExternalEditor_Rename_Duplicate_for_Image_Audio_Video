# License AGPLv3, see main

import os
import re
import subprocess 

from anki.utils import isMac,isWin,isLin
from aqt import mw
from aqt.editor import Editor

from .helper import process_path


def gc(arg,fail=False):
    return mw.addonManager.getConfig(__name__).get(arg,fail)


def open_in_external(fileabspath,external_program):
    if isMac:
        open_command = "open "
        if external_program:
            open_command += '-a %s ' % external_program
        fileabspath = re.sub(" ","\ ",fileabspath)
        os.system(open_command + fileabspath)
    else:
        #subprocess.Popen(external_program + " \"" + fileabspath + "\" ", shell = True) 
        subprocess.Popen([external_program, fileabspath])


def _editExternal(editor,fname,type,field):
    mediafolder, fileabspath, base, ext = process_path(fname)
    #detection of file type with proper library might require
    #external dependencies and/or relicesing. That's quicker.
    if type == "image":
        external_program = gc("image_edit_externally__program")
        if gc("image_edit_externally__block_Anki_during_edit") and not isMac:
            subprocess.check_output([external_program,fileabspath])
            editor.saveTags()
            editor.web.page().profile().clearHttpCache()
            # editor.outerLayout.itemAt(0).widget().setParent(None)
            # editor.outerLayout.itemAt(0).widget().setParent(None)
            # editor.setupWeb()  
            # editor.setupTags()
            editor.loadNote(focusTo=field)
    elif type == "sound":
        if ext.lower()[1:] in gc("sound__extensions_audio"):   # ext has leading "."
            external_program = gc("sound__external_program_audio")
        else:
            external_program = gc("sound__external_program_video")
        if external_program:
            open_in_external(fileabspath,external_program)



def reviewer_context_edit_img_external(view,fname):
    mediafolder, fileabspath, base, ext = process_path(fname)
    external_program = gc('image_edit_externally__program')
    #mw.reviewer.web.eval("document.activeElement.blur();")  #?
    if gc("image_edit_externally__block_Anki_during_edit") and not isMac:
        subprocess.check_output([external_program,fname])
        ##the similar function for the editor works but not here
        #view.page().profile().clearHttpCache()
        mw.reset(guiOnly=True)   #?
    else:
        open_in_external(fileabspath,external_program)
