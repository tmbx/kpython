#!/usr/bin/env python

# Stand-alone process monitor.
#
# Starts processes that do not detach from the terminal, and respawn them when
# they die, after a short delay.

import sys, getopt, signal, socket

sys.path.append("/usr/share/python-support/kpython")
from kbase import *
from kfile import *
from kout import *
from kdaemonize import *


# Configuration.

# The respawn delay of the child, in seconds.
child_respawn_delay = 10

# The time to wait for the child to exit normally, in seconds.
term_timeout = 5


# Globals.

# The PID of the child, if any.
child_pid = None

# The time at which the child last exited.
child_last_exit_time = 0

# The socket pair created to wake up the main thread when a signal is received.
# Write to the first socket, read from the second.
wakeup_pair = None

# This flag is set when SIGTERM has been received.
got_sigterm = 0

# This function calls waitpid() and returns true if the specified process has
# exited.
def call_waitpid(pid):
    ret = os.waitpid(pid, os.WNOHANG)
    return ret[0] == pid

# This function waits for the process specified to exit for the specified number
# of seconds. It returns 1 if the process exited and 0 if a timeout occurred.
def wait_for_exit(pid, timeout):
    init_time = time.time()
    
    while 1:
	# Wait for the process.
	if call_waitpid(pid): return 1
	
	# Compute time to wait.
	time_to_wait = init_time + timeout - time.time()
	if time_to_wait < 0: return 0
	
	# Wait for signal to happen.
	try: select_wrapper([], [], [], time_to_wait + 0.01)
	except: pass

# This function stops the current child if it is running, first by sending it
# SIGTERM then by sending it SIGKILL.
def stop_child():
    global child_pid
    
    # No child is running.
    if child_pid == None: return
    
    # Send SIGTERM.
    out("Sending SIGTERM to child process %i." % (child_pid))
    os.kill(child_pid, signal.SIGTERM)
    
    # The child has exited normally.
    if wait_for_exit(child_pid, term_timeout):
	out("Child process %i terminated normally." % (child_pid))
	child_pid = None
	return
    
    # Send SIGKILL.
    out("Sending SIGKILL to child process %i." % (child_pid))
    os.kill(child_pid, signal.SIGKILL)
    call_waitpid(child_pid)
    child_pid = None

# This function is the signal handler for SIGTERM.
def sigterm_handler(signum, frame):
    global got_sigterm
    global wakeup_pair
    
    out("Caught SIGTERM.")
    
    # Set the sigterm flag first.
    got_sigterm = 1
    
    # Wake up the main thread.
    try: wakeup_pair[0].write('a')
    except: pass

# This function is the signal handler for SIGCHLD.
def sigchld_handler(signum, frame):
    global got_sigterm
    global wakeup_pair
    
    debug("Caught SIGCHLD.")
    
    # Wake up the main thread.
    try: wakeup_pair[0].write('a')
    except: pass

# This function runs the command specified.
def run_command(command):
    global child_pid
	
    pid = os.fork()
    
    # Child.
    if pid == 0:
	try: os.execv(command[0], command[0:])
	except Exception, e: err("Exec failure: %s." % (str(e)))
	os._exit(1)
	
    # Parent.
    elif pid > 0:
	child_pid = pid

# This function monitors the process specified, respawning it when it fails.
def monitor_process(command):
    global wakeup_pair
    global child_pid
    global child_last_exit_time

    # Register the signal handlers.
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGCHLD, sigchld_handler)
    
    # Create the socket pair.
    wakeup_pair = socket.socketpair()
    wakeup_pair[0].setblocking(0)
    wakeup_pair[1].setblocking(0)
    
    # Loop until we're done.
    while 1:
	# Time to wait in select().
	time_to_wait = 0
	
	# A child was spawned.
	if child_pid != None:
	
	    # The child has exited. Re-run the loop immediately.
	    if call_waitpid(child_pid):
		err("Child %d exited unexpectedly." % (child_pid))
		child_pid = None
		child_last_exit_time = time.time()
	    
	    # Wait for something to happen.
	    else:
		time_to_wait = 10000
	
	# No child was spawned.
	else:
	    # Compute the time elapsed since the child exited.
	    ttw = child_last_exit_time + child_respawn_delay - time.time()
	    
	    # It is time to spawn the child.
	    if ttw <= 0:
		out("Running command %s, params: %s." % (command[0], command[1:]))
		run_command(command)
	    
	    # We must wait a bit before respawning the child.
	    else:
		time_to_wait = ttw
	
	# Wait for something to happen.
	select_wrapper([wakeup_pair[1]], [], [], time_to_wait + 0.01)
	
	# Read everything written on the wakeup socket.
	while 1:
	    try: wakeup_pair[1].recv(100)
	    except socket.error, e:
		check_interrupted_ex(e)
		break
	
        # We must exit. Stop the child if it is running, and return.
	if got_sigterm:
	    stop_child()
	    return

def usage():
    s = "Usage: " + sys.argv[0] + " [options] <command> [command_params]\n" +\
        " Options:\n" +\
        " -d, --debug:                            prints debug informations\n" +\
        " --delay:                                delay before respawning process\n" +\
        " -t, --daemonize:                        daemonize\n" +\
        " -p <pidfile>, --pidfile <pidfile>:      write pid to file\n" +\
        " --term-timeout <seconds>:               timeout when terminating child\n" +\
	"                                           before sending SIGKILL.\n" +\
	"\n"
    out(s)

def main():
    global child_respawn_delay 
    global term_timeout
    ret_code = 0
    
    try:
	opts, args = getopt.getopt(sys.argv[1:], "dtp:", ["debug", "delay=", "daemonize", "pidfile=", "term-timeout="])
    except getopt.GetoptError, e:
	sys.stderr.write("Options error: '%s'\n" % (str(e)) )
	usage()
	os._exit(1)

    detach = False
    pidfile = None
    dodebug = False # debug is a function imported from kout.

    for k, v in opts:
	if k == "-d" or k == "--debug":
	    dodebug = True
	elif k == "--delay":
	   child_respawn_delay = int(v)
	elif k == "-t" or k == "--daemonize":
	    detach = True
	elif k == "-p" or k == "--pidfile":
	    pidfile = v
	elif k == "--term-timeout":
	    term_timeout = int(v)
	    
    command = args
    if len(command) < 1:
	usage()
	os._exit(1)

    # Enable debug.
    if dodebug:
	do_debug()

    # Daemonize of option was set.
    if detach:
	# Redirect out, err and debug to syslog.
	do_logredirect()

	# Daemonize.
	daemonize()

    # Write PID file if asked to do so.
    if pidfile:
	pid = os.getpid()
	debug("Writing pid to '%s'" % (pidfile))
	try: write_file(pidfile, str(pid))
	except Exception, e:
	    err("Could not write pid file '%s': %s" % (pidfile, str(e)) )
	    err("Exiting.")
	    os._exit(1)

    # Respawn command until sun dies.
    try: monitor_process(command)
    except Exception, e:
	err("Monitoring process failed: %s." % (str(e)))
	ret_code = 1
    
    # Delete the PID if required.
    if pidfile: delete_file(pidfile)
    
    # Exit.
    os._exit(ret_code)

if __name__ == "__main__":
    main()

