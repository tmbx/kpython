# This module contains code to prompt the user for stuff in console mode.

from kbase import *
import readline

# This class setups command completion in readline.
class readline_completer:
    def __init__(self, words):
        self.words = words
        self.prefix = None
	
    def complete(self, prefix, index):
        if prefix != self.prefix:
            self.matching_words = [ w for w in self.words if w.startswith(prefix) ]
            self.prefix = prefix
        try:
            return self.matching_words[index]
        except IndexError:
            return None

# This function prompts the user for a confirmation (y/n). It returns true if
# the confirmation was given. Note: I wrote this on a friday evening.
def get_confirm(prompt):
    try:
	while 1:
	    res = raw_input(prompt + " ")
	    res = string.lower(res)
	    
	    if (res == "yes" or res == "aye" or res == "sure" or res == "of course" or\
		res == "go ahead" or res == "why not" or res == "yeah" or res == "y"): return 1
	    if (res == "no" or res == "nay" or res == "nah" or res == "never" or res == "n"): return 0
	    
	    print "Please answer with 'y' or 'n'.\n"
	    
    except Exception:
	print ""
	raise KeyboardInterrupt

# This function prompts the user for a string. It returns the string entered,
# which can be "". The string is stripped of its surrounding whitespaces.
def prompt_string(prompt):
    try: return raw_input(prompt + " ").strip()
    except Exception:
	print ""
	raise KeyboardInterrupt
