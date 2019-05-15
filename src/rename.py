# License AGPLv3, see main
# * rename.apply_to_notes uses code from Audio Renamer which is covered by 
# * the following copyright and permission notice:  
# *  
# * @author: mkpoli
# * https://github.com/mkpoli
# * License WTFPL


import os
import time

from aqt import mw
from aqt.utils import tooltip

from .helper import (
    process_path, 
    get_unused_new_name, 
    replace_sound_in_editor_and_reload,
    replace_img_in_editor_and_reload
)

def gc(arg,fail=False):
    return mw.addonManager.getConfig(__name__).get(arg,fail)


def backup_rename(changednids,renamedfiles):
    addon_dir_path = os.path.join(os.path.dirname(__file__))
    now = time.strftime('%Y-%m-%d__%H_%M_%S', time.localtime(time.time()))
    #user_files is not overwritten on update, see addons.py#229 _install()
    backupdir = os.path.join(addon_dir_path,"user_files","backups_renameImageSound",now)
    fieldsdir = os.path.join(backupdir,"fieldcontents")
    if not os.path.isdir(fieldsdir):
        os.makedirs(fieldsdir)
    csv_file = os.path.join(backupdir,"renamed_files.csv")
    with open(csv_file, 'w') as f:
        for k,v in renamedfiles.items():
            f.write("%s\t%s\n"%(k,v))
    for k,v in changednids.items():
        nidfile = os.path.join(fieldsdir,str(k) + '.txt')
        with open(nidfile,"w") as f:
            f.write(v)


def apply_to_notes(old,new,type):
    rpls = {}
    if type == "sound":
        rpls[':' + old] = ':' + new
    elif type == "image":  
        rpls['src="' + old] = 'src="' + new
        #sometimes people use img src='
        rpls["src='" + old] = "src='" + new

    changednids = {}
    renamedfiles = {}
    for r in mw.col.db.execute("select id, flds from notes"):
        nid = r[0]
        allFldsContent = r[1]
        for _old,_new in rpls.items():
            if _old in allFldsContent: 
                changednids[nid] = allFldsContent   
                newFlds = allFldsContent.replace(_old, _new)
                updateQuery = "UPDATE notes SET flds=? WHERE id=?"
                mw.col.db.execute(updateQuery, newFlds, nid)
                #this is not foolproof: I assume that the same file is not referenced twice
                #in the same note with different notations ("" vs '')
                if not os.path.isfile(new):
                    os.rename(old, new)
                    renamedfiles[old] = new
    if gc("backup_on_rename",True):
        backup_rename(changednids,renamedfiles)
    modNids  = str([a for a in changednids.keys()])
    modFiles = str([a for a in renamedfiles.keys()])
    status = 'changed nids: %s, renamed files: %s' % (modNids, modFiles)
    tooltip(status)


def _rename(editor,fname,type,field):
    mediafolder, fileabspath, base, ext = process_path(fname)
    if os.path.isfile(fileabspath):   #verify
        newfilename = get_unused_new_name(mediafolder,base,ext)
        if newfilename:
            # mw.col.findNotes doesn't help because filenames may contain "()" and ":"
            # which don't work with search
            # so findReplace which needs a list of nids doesn't work
            apply_to_notes(fname, newfilename,type)

            #update fields
            if type == "sound":
                searchstring  = '[sound:' + fname        + ']'
                replacestring = '[sound:' + newfilename  + ']'
                replace_sound_in_editor_and_reload(editor,searchstring,replacestring,field)
            elif type == "image":
                replace_img_in_editor_and_reload(editor,fname,newfilename,"rename",field)
