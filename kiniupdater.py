#!/usr/bin/env python

# MISSING DOCUMENTATION!!!!!

#
# MISC ini config updater
# allows replacements in ini files (will drop the comments!!)
#
# --input can be '-' or a file (file can be /dev/null...)
# --output can be '-' or a file (can be the same file as input if you want.. it's safe))
# --set, --delete: X is a seperating character (like ':')
# --fill: ask for the value in a sample question.. can provide a default value too.
#
# WARNING: updating your ini file with this program will screw the sections/keys order and will strip your comments
#
# notes:
#   - there is no --get... it's kiniupdater... not kiniqueryer :)
#   - you can provide only one input and one output... 
#   - I did this on my spare time, so don't complain if you think it is useless
#

import sys
import os
import ConfigParser
import StringIO
import getopt

def parse(s):
    c = ConfigParser.RawConfigParser()  # use this instead of ConfigParser so it won't do
                                        # magical interpolation (see http://docs.python.org/lib/module-ConfigParser.html)
    fp = StringIO.StringIO(s)
    c.readfp(fp)
    return c

def loadfile(file):
    c = ConfigParser.RawConfigParser()  # see comment above: http://docs.python.org/lib/module-ConfigParser.html
    c.read(file)
    return c

def usage():
    print ("Usage: %s" \
        + " [-i|--input <input file>]" \
        + " [-o|--output <output file>]" \
        + " [-s|--set X<section>X<var>X<value>]..." \
        + " [-d|--delete X<section>[X<key>]]..." \
        + " [-f|--fill X<section>X<key>[X<default value>]...") \
        % (sys.argv[0])

def error_exit(s):
    sys.stderr.write(s + "\n")
    sys.exit(1)

# class for parsing get and set arguments
# arguments must have a section; key and value are optional
class Config:
    def __init__(self, section=None, key=None, value=None, parse_str=None):
        self.section = section
        self.key = key
        self.value = value
        if parse_str:
            self.parse(parse_str)
    
    section = property()
    key = property()
    value = property()

    def parse(self, s):
        char = s[0]
        parts = s.split(char)
        parts.pop(0)
        for part in parts:
            if len(part) == 0:
                raise Exception("Invalid confif: %s" % (s) )
        if len(parts) > 3:
            raise Exception("Invalid config: %s" % (s) )
        if len(parts) == 3:
            [self.section, self.key, self.value] = parts
        elif len(parts) == 2:
            [self.section, self.key] = parts
        else:
            [self.section] = parts
    

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:s:d:f:", ["help", "input=", "output=", "set=", "delete=", "fill="])
    except getopt.GetoptError, e:
        sys.stderr.write("Options error: '%s'\n" % (str(e)) )
        usage()
        sys.exit(1)

    input = None
    output = None
    setlist = []
    deletelist = []
    filllist = []

    for k, v in opts:
        if k == "-h" or k == "--help":
            usage()
            sys.exit(0)
        elif k == "-i" or k == "--input":
            if input:
                error_exit("Only one input file must be set.")
            input = v
        elif k == "-o" or k == "--output":
            if output:
                error_exit("Only one output file must be set.")
            output = v
        elif k == "-s" or k == "--set":
            try:
                c = Config(parse_str=v)
                if not c.section or not c.key or not c.value:
                    error_exit("Invalid config '%s' for setting." % (v) )
                else:
                    setlist.append(c)
            except Exception, e:
                error_exit(str(e))
        elif k == "-d" or k == "--delete":
            try:
                c = Config(parse_str=v)
                if not c.section or c.value:
                    error_exit("Invalid config '%s' for deleting." % (v) )
                else:
                    deletelist.append(c)
            except Exception, e:
                error_exit(str(e))
        elif k == "-f" or k == "--fill":
            try:
                c = Config(parse_str=v)
                if not c.section or not c.key:
                    error_exit("Invalid config '%s' for filling." % (v) )
                else:
                    filllist.append(c)
            except Exception, e:
                error_exit(str(e))


        else:
            error_exit("Invalid option '%s'" % (k))
    
    if len(args) > 0:
        error_exit("No arguments expected.")
    
    if not input or input == "-":
        if len(filllist) > 0:
            error_exit("Can't fill values when getting config from stdin...")
        c = parse(sys.stdin.read())
    else:
        c = loadfile(input)

    toclose = False
    if not output or output == "-":
        outputfd = sys.stdout
    else:
        toclose = True
        outputfd = open(output, "w")

    for config in setlist:
        if not c.has_section(config.section):
            c.add_section(config.section)
        c.set(config.section, config.key, config.value)

    for config in deletelist:
        if config.key:
            if c.has_section(config.section) and c.has_option(config.section, config.key):
                c.remove_option(config.section, config.key)
        else:
            if c.has_section(config.section):
                c.remove_section(config.section)

    for config in filllist:
        default = ''
        if c.has_section(config.section) and c.has_option(config.section, config.key):
            default = c.get(config.section, config.key)
        if config.value:
            default = config.value
        ret = 0
        while 1:
            newval = raw_input("What value for section '%s', key '%s' (default value is '%s')? Press enter to accept... " % (config.section, config.key, default))
            if newval == "":
                c.set(config.section, config.key, default)
                break
            else:
                default = newval
                    

    c.write(outputfd)
    if toclose:
        outputfd.close()


if __name__ == "__main__":
    main()

