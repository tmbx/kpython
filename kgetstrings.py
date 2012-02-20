#!/usr/bin/env python

# Preliminary module to get strings support.
# Will probably update to gettext later when we want multi-languages support.

# from kpython
import kdebug

# This function gets a translated and "non-altered" string for <application>. If string is not existant,
# it will be replaced by "MISSING:<key>" or by None (depending on <none_if_missing> value).
def get_string(strings, key, app=None, none_if_missing=False):
    kdebug.debug(1, "set_strings(key='%s', app='%s', none_if_missing='%s'" % \
        ( key, str(app), str(none_if_missing) ), "kgetstrings" )

    if strings and strings.has_key(app) and strings[app].has_key(key):
        return strings[app][key]
        
    if none_if_missing == True:
        return None

    return "MISSING:"+key

# un-exhaustive tests
if __name__ == "__main__":
    strings = { }

    print get_string(strings, "lalala")
    print get_string(strings, "lalala", none_if_missing=True)

    strings = { "app1" : { "lala" : "La La", "lili" : "Li Li" } }
    
    print get_string(strings, "lala")
    print get_string(strings, "lala", app="app1")


