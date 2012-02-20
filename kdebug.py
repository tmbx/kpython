#!/usr/bin/env python

"""
Pluggable debug

This module allows pluggable debugging (changing debug output function or class method at run-time) and to
change debugging settings for every module (that is using kdebug) from a single application.

By default, debug is disabled. When debug is enabled, default debug level is 1.

Lets say you're coding an application that uses module "dummy" as a library,
and both the application and the "dummy" module use kdebug:
when debugging, you can tune debug settings for both the application and the "dummy" module.
> kdebug.set_debug_level(0) --> main application debug
> kdebug.set_debug_level(9, "dummy") --> dummy module
Every call to a kdebug function in the "dummy" module must use "dummy" as the debug_id.

For this and for the pluggable feature to work, every module must use the same kdebug "instance", so must:
>   import kdebug
instead of:
>   from kdebug import *  # which appears to load a kdebug "instance" for every module
"""

import sys, inspect

# default ID
DEFAULT_ID="main"

# initialize
last_debug_level = {DEFAULT_ID : None}
debug_level = {DEFAULT_ID : None} 

def enable_debug(debug_id=DEFAULT_ID):
    """
    Enable debug for debug_id
    """

    debug_id = str(debug_id)
    global last_debug_level
    if last_debug_level.has_key(debug_id) and last_debug_level[debug_id] and last_debug_level[debug_id] > 0:
        # Use last debug level
        set_debug_level(last_debug_level[debug_id], debug_id)
    else:
        # Use debug level 1
        set_debug_level(1, debug_id)


def disable_debug(debug_id=DEFAULT_ID):
    """
    Disables debug for debug_id
    """

    debug_id = str(debug_id)
    set_debug_level(0, debug_id)


def is_debug_enabled(debug_id=DEFAULT_ID):
    """
    Checks wheither debug is enabled or not for debug_id
    """

    debug_id = str(debug_id)
    return (get_debug_level(debug_id) > 0)


def set_debug_level(level, debug_id=DEFAULT_ID):
    """
    Sets the current debug level for debug_id
    Level must be a positive integer (including 0)
    Set to 0 to disable debugging
    """

    debug_id = str(debug_id)
    if level < 0:
        raise Exception("Invalid level. Must be an positive integer (including 0).")
    if level == 0:
        global debug_level
        global last_debug_level
        if debug_level.has_key(debug_id) and debug_level[debug_id] > 0:
            last_debug_level[debug_id] = debug_level[debug_id]
    debug_level[debug_id]= level

def set_debug_levels(d):
    """
    Sets current debug levels with a dictionnary.
    """

    for debug_id, level in d.items():
        set_debug_level(level, debug_id)

def get_debug_level(debug_id=DEFAULT_ID):
    """
    Returns the current debug level for debug_id
    """

    debug_id = str(debug_id)
    global debug_level
    if debug_level.has_key(debug_id):
        return debug_level[debug_id]
    return 0

def would_debug(level, debug_id=DEFAULT_ID):
    """
    Returns weither to debug or not depending on the provided and current level.
    """

    debug_id = str(debug_id)
    if int(level) < 1:
        raise Exception("You must use a level > 0.")
    if is_debug_enabled(debug_id) and int(level) <= int(get_debug_level(debug_id)):
        return True
    return False

def debug(level, message, debug_id=DEFAULT_ID):
    """
    Default function
    """

    debug_id = str(debug_id)
    if would_debug(level, debug_id):
        debug_output_callable("debug:%i:%s:%s" % (level, debug_id, message) )

def debug_default_callable(m):
    """
    Default debug output function
    """

    sys.stdout.write(m + "\n")


def set_debug_callable(c):
    """
    Set debug output callable (function, class method)
    """

    global debug_output_callable
    debug_output_callable = c


# default debug function
set_debug_callable(debug_default_callable)


# non-exhaustive tests
if __name__ == "__main__":
    debug(1, "You should not see this - 1.")
    enable_debug()
    debug(1, "You should see this - 2.")
    set_debug_level(2)
    debug(3, "You should not see this - 3.")
    debug(1, "You should see this - 3.")
    debug(2, "You should see this - 4.")
    debug(3, "You should not see this - 5.")
    debug(4, "You should not see this - 6.")
    disable_debug()
    debug(8, "You should not see this - 7.")
    set_debug_level(4)
    debug(4, "You should see this - 8.")
    disable_debug()
    debug(4, "You should not see this - 9.")
    enable_debug()
    debug(4, "You should see this - 10.")
    debug(5, "You should not see this 11", "libx")
    set_debug_level(5, "libx")
    debug(5, "You should see this - 12.", "libx")


