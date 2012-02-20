# This module contains code that manage files.

import os, stat, hashlib
from kbase import *
from tempfile import mkstemp
import krun, ConfigParser

# This function writes the data specified to the file specified.
def write_file(path, data):
    check_file_writable(path, 1)
    f = open(path, "wb")
    f.write(data)
    f.close()

# This function writes the content of a file atomically by using a temporary
# file. The permissions of the destination file are preserved by default,
# otherwise the mode 644 is used.
def write_file_atom(path, data, preserve_flag=1):
    
    # Note that mkstemp creates the file with the mode 600.
    (unix_fileno, tmp_path) = mkstemp(dir=os.path.dirname(path))
    tmp_file = os.fdopen(unix_fileno, "wb")
    tmp_file.write(data)
    tmp_file.close()
    
    try:
        if os.path.isfile(path):
            dest_stat = os.stat(path)
            os.chmod(tmp_path, stat.S_IMODE(dest_stat.st_mode))
            os.chown(tmp_path, dest_stat.st_uid, dest_stat.st_gid)
        else:
            os.chmod(tmp_path, 0644)
    except: pass
    
    os.rename(tmp_path, path)

# Move a file atomically and preserve the permissions and ownership information
# of the destination file, if it exists, if requested (disabled by default) and
# if possible.
def move_file(src, dest, preserve_flag=0):
    if preserve_flag and os.path.isfile(dest):
        try:
            dest_stat = os.stat(dest)
            os.chmod(src, stat.S_IMODE(dest_stat.st_mode))
            os.chown(src, dest_stat.st_uid, dest_stat.st_gid)
        except: pass
    os.rename(src, dest)
    
# This function reads and returns the data contained in the file specified.
def read_file(path):
    check_file_readable(path, 1)
    f = open(path)
    data = f.read()
    f.close()
    return data

# This function returns true if the file specified is readable. Optionally, an
# exception is thrown if the file is not readable.
def check_file_readable(file, raise_on_error=True):
    if type(file) != str:
        raise Exception("bad parameter")

    if not os.path.exists(file):
        if raise_on_error == False:
            return False
        raise Exception("file '%s' does not exist" % (file))

    if not os.access(file, os.R_OK):
        if raise_on_error == False:
            return False
        raise Exception("file '%s' is not readable" % (file))

    return True

# Same as above.
def check_file_writable(file, raise_on_error=True):
    if type(file) != str:
        raise Exception("bad parameter")

    dir = os.path.dirname(file)
    if (dir == ''): dir = '.'

    if not os.path.exists(dir):
        if raise_on_error == False:
            return False
        raise Exception("directory '%s' does not exists" % (dir))

    if os.path.exists(file):
        if not os.access(file, os.W_OK):
            if raise_on_error == False:
                return False
            raise Exception("file '%s' is not writable" % (file))
    else:
        if not os.access(dir, os.W_OK):
            if raise_on_error == False:
                    return False
            raise Exception("dir '%s' is not writable" % (dir))

    return True

# This function deletes a file if it exists.
def delete_file(path):
    if os.path.isfile(path): os.remove(path)

# This returns the MD5 sum of a file.
def file_md5(file):
    m = hashlib.md5()
    f = open(file, 'r')
    while 1:
        data = f.read(65536)
        if not data: break
        m.update(data)
    f.close()
    return m.digest()

# This function reads a ConfigParser object representing an INI file.
def read_ini_file(path):
    f = open(path, "rb")
    parser = ConfigParser.ConfigParser()
    parser.readfp(f)
    f.close()
    return parser

# This function writes the content of a ConfigParser object into an INI file
# atomically. The permissions of the destination file are preserved by default.
def write_ini_file(path, parser, preserve_flag=1):
    (unix_fileno, tmp_path) = mkstemp()
    tmp_file = os.fdopen(unix_fileno, "wb")
    parser.write(tmp_file)
    tmp_file.close()
    move_file(tmp_path, path, preserve_flag)
    
# This function throws an exception if the specified file does not exist.
def assert_file_exist(path):
    if not os.path.isfile(path): raise Exception("file '%s' does not exist" % (path))

# This function throws an exception if the specified directory does not exist.
def assert_dir_exist(path):
    if not os.path.isdir(path): raise Exception("directory '%s' does not exist" % (path))

# Append a slash to the path specified if the path is not "" and it does not end
# with a slash.
def append_trailing_slash(path):
    if path != "" and not path.endswith("/"): return path + "/"
    return path

# Remove any trailing slash from the path specified unless the path is '/'.
def strip_trailing_slash(path):
    if path != "/" and path.endswith("/"): return path[:-1]
    return path

# This function filters the specified file with the specified list of (pattern,
# replacement) pairs. If a pattern matches, the current line is replaced by the
# associated replacement string. If the replacement string is 'None', the
# current line is discarded. If no pattern matches the current line, the line is
# added back as-is.
def filter_generic_config_file(path, pair_list):
    data = ""
    f = open(path, "rb")
    
    for line in f.readlines():
        line = line.rstrip("\n")
        matched_flag = 0
        
        for pair in pair_list:
            regex = re.compile(pair[0])
            if regex.search(line):
                matched_flag = 1
                if pair[1] != None: data += regex.sub(pair[1], line) + "\n"
                break
         
        if not matched_flag:
            data += line + "\n"
    
    f.close()
    write_file_atom(path, data)

# Return the first existing file from the list.
def first_existing_file(file_list):
    for file in file_list:
        if os.path.isfile(file):
            return file
    return None

if __name__ == "__main__":
    # run some INCOMPLETE tests...
    # read
    print "readable (should be 0): %i" % check_file_readable("/etc/passwdfsdfsdfs", False)
    print "readable (should be 1): %i" % check_file_readable("/etc/passwd", False)
    ## print "len (should be 0): %i" % len(read_file("/etc/passwdsdfsdfsdf"))
    print "len (should be >0): %i" % len(read_file("/etc/passwd"))

    # write
    print "writable (should be 0) %i: " % check_file_writable("/tmp/fgsdfsd/gdfgfdg/gsdfgdfg", False)
    print "writable (should be 1) %i: " % check_file_writable("/tmp/passwdsdfdsf", False)
    print "writable (should be 0) %i: " % check_file_writable("/etc/passwd", False)

    write_file("/tmp/lalalalala", "123456")
    t = read_file("/tmp/lalalalala")
    if len(t) == len("123456"):
        print "write ok"
    else:
        print "write failed"

    try:
        read_file("/tmp/lalala/lilili/lololo/aaaaaa")
        print "could read un unreadable file!!"
    except Exception, e:
        print "read failed like excepted: %s" % str(e)

    try:
        write_file("/tmp/lalala/lilili/lololo/aaaaaa", "lalala")
        print "could write an unwritable file!!"
    except Exception, e:
        print "write failed like expected: %s" % str(e)

