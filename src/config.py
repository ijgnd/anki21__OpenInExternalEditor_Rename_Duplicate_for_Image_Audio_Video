from aqt import mw


def gc(arg, fail=False):
    conf = mw.addonManager.getConfig(__name__)
    if conf:
        return conf.get(arg, fail)
    else:
        return fail

from anki import version as anki_version

_, _, point = anki_version.split(".")
pointversion = int(point)
