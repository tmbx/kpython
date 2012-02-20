# Access privileged stuff using sudo.

import os
from tempfile import mkstemp

# from kpython
from krun import get_cmd_output

# Read file and return its content.
def read_file(file_path):
    return get_cmd_output(['sudo', 'cat', file_path])

# This function writes the content of a file atomically by using a temporary
# file. The permissions of the destination file are preserved by default.
def write_file_atom(path, data, preserve_flag=1):
    umask = os.umask(0777)
    try:
        (unix_fileno, tmp_path) = mkstemp()
        tmp_file = os.fdopen(unix_fileno, "wb")
        tmp_file.write(data)
        tmp_file.close()
        move_file(tmp_path, path, preserve_flag)
    finally:
        os.umask(umask)

# Move a file atomically and preserve the permissions and ownership information
# of the destination file, if it exists, if requested (disabled by default) and
# if possible.
def move_file(src, dest, preserve_flag=0):
    if preserve_flag and os.path.isfile(dest):
        try:
            dest_stat = os.stat(dest)
            get_cmd_output(['sudo', 'chown', '%i:%i' % (dest_stat.st_uid, dest_stat.st_gid), src])
            get_cmd_output(['sudo', 'chmod', oct(dest_stat.st_mode)[-4:], src])
        except:
             pass
    get_cmd_output(['sudo', 'mv', '-f', src, dest]) 


