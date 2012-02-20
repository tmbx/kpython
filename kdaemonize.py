#!/usr/bin/python

from kbase import *

def daemonize(workdir='/', umask=022, maxfd=1024):
    pid = os.fork()
    
    # Parent process.
    if pid != 0: os._exit(0)

    # This is the first child.

    # Get new process group.
    os.setsid()
    
    # Misc.
    os.chdir(workdir)
    os.umask(umask)

    # Close filedescriptors.
    for fd in range(0, maxfd): # Should get maxfd from os module.
        try:
             os.close(fd)
        except OSError:
            # FD was not opened.. it's ok.
            pass

    os.open("/dev/null", os.O_RDWR)	# standard input (0)
    os.dup2(0, 1)			# standard output (1)
    os.dup2(0, 2)			# standard error (2)


if __name__ == "__main__":

    daemonize()

    import time	
    time.sleep(10)

    sys.exit(0)


