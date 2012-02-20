# This module imports some standard Python libraries and defines some basic
# functions and objects.

# Import standard libraries.
import os, sys, string, re, time, random, select, errno

# This class creates an object having the specified attributes.
# Example: person = Namespace(name="Mickey", age=18)
class Namespace(object):
    def __init__(self, **kwds): self.__dict__ = kwds

# This class creates an object in which it is possible to add fields
# dynamically. Example: store = PropStore(); store.foo = "bar"
class PropStore(object):
    
    def __setattr__(self, name, value):
        self.__dict__[name] = value
    
    def __getattr__(self, name):
        if not self.__dict__.has_key(name): raise AttributeError, name
        return self.__dict__[name]
    
    def __setitem__(self, name, value):
        self.__dict__[name] = value
    
    def __getitem__(self, name):
        if not self.__dict__.has_key(name): raise KeyError, name
        return self.__dict__[name]
    
    def __delitem__(self, name):
        del self.__dict__[name]
    
    def has_key(self, name):
        return self.__dict__.has_key(name)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def to_dict(self):
        return self.__dict__

    def from_dict(self, dict):
        self.__dict__ = {}
        for key, value in dict.items():
            self.__dict__[key] = value
        return self

# This function returns true if the string specified is alphanumeric (a-z, 0-9,
# '_'). This is a workaround for Python's unexpected implementation.
def isalpha(s):
    return s.replace('_', '').isalnum()

# This function adds spaces to the string specified until the total length of
# the string is at least 'min'.
def fill_string(s, min):
    while len(s) < min: s += ' '
    return s
    
# This function converts a string to hexadecimal. Function taken from the Python
# Cookbook.
def str_to_hex(s):
    lst = []
    for ch in s:
        hv = hex(ord(ch)).replace('0x', '')
        if len(hv) == 1:
            hv = '0'+hv
        lst.append(hv)
    
    return reduce(lambda x,y:x+y, lst)

# This function converts an hexadecimal number to a string.
def hex_to_str(s):
    return s and chr(string.atoi(s[:2], base=16)) + hex_to_str(s[2:]) or ''

# This function converts an ISO-8859-1 string to an UTF8 string.
def latin1_to_utf8(name):
    res = ""
    for c in name:
        o = ord(c)
        if (o < 128):
            res += c
        else:
            res += chr(0xC0 | ((o & 0xC0) >> 6))
            res += chr(0x80 | (o & 0x3F))
    return res

# This function generates a random string, suitable for a username or password.
def gen_random(nb):
    generator = random.SystemRandom()
    s = ""
    
    for i in range(nb):
        s += generator.choice(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
                               'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                               '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])
    return s

# This function checks if the exception specified corresponds to EINTR or
# EAGAIN. If not, the exception is raised.
def check_interrupted_ex(e):
    if e.args[0] != errno.EINTR and e.args[0] != errno.EAGAIN: raise e

# This function is a wrapper around select.select() to give it sane semantics.
def select_wrapper(rlist, wlist, xlist, timeout):
    try: return select.select(rlist, wlist, xlist, timeout)
    except select.error, e:
        check_interrupted_ex(e)
        return ([], [], [])

# This is a mixed class is an attribute store that:
# - enforces read-only attributes if attribute name is in self._attr_read_only)
# - checks attribute value type if attribute name is in self._attr_type_definitions[type]
#   (tested only with those types yet: bool, int, list, str, dict
# - allows attributes of any types if attribute name is in self._attr_any_type_definitions
# - doesn't allow non-defined attributes
class DefinedAttributesStore(object):
    ## SUPER ME ##
    def __init__(self):
        # init config vars
        self._attr_read_only = []
        self._attr_type_definitions = {bool : [], int : [], list : [], str : [], dict : []}
        self._attr_any_type_definitions = []

    # set attribute if definitions match, or raise TypeError
    def __setattr__(self, name, value):
        # allow built-in config vars
        if name in [ "_attr_read_only", "_attr_type_definitions", "_attr_any_type_definitions" ]:
            self.__dict__[name] = value
            return

        # check if attribute is read-only
        if name in self._attr_read_only:
            raise AttributeError, name

        # check if attribute is defined in basic types dict
        for attr_type, attr_list in self._attr_type_definitions.items():
            if name in attr_list:
                if type(value) != attr_type:
                    raise TypeError, "Attribute '%s' expects values of type '%s'." % ( name, attr_type )
                self.__dict__[name] = value
                return

        # check if attribute is defined in the any_type list
        if name in self._attr_any_type_definitions:
            self.__dict__[name] = value
            return

        # no chance
        raise AttributeError, name


# This function validates that string does not contains a character in the provided list.
# Characters list must contain integers representing characters.
# This function is NOT multi-byte character compatible.
def validate_string_chars(s, bad_chars):
    for bad_char in bad_chars:
        for c in s:
            if c == chr(bad_char):
                return False
    return True
    
