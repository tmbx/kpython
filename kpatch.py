#!/usr/bin/env python

import sys
import subprocess

# This function patches a file with a patch string.
def handle_apply_patch(file, patch, opts=None, out=sys.stdout, err=sys.stderr):
    # Build the patch command array.
    if opts: cmd = ["patch"] + opts + [file]
    else: cmd = ["patch"] + [file]

    # Send the patch string as stdin to the 'patch' command.
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(patch)

    # Handle result of the command.
    if proc.returncode == 0:
        if out:
            out.write("Successfully patched file %s.\n" % ( file ) )
        sys.exit(0)
    if out:
        out.write("Failed to patch file %s.\n" % ( file ) )
        out.write(stdout)
    if err:
        err.write(stderr)
    sys.exit(1)

