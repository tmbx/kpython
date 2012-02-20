#####
##### OUTPUT AND DEBUG
#####

import sys


from klog import *

# all output and debugging can be output to a log with the logredirect option
# this is useful when we call functions from a web interface

# don't redirect output to log by default
try:
	junk = logredirect_enable
except:
	logredirect_enable = False

# can be called from another script to enable logredirect
def do_logredirect():
	global logredirect_enable
	logredirect_enable = True

# can be called from another script to disable logredirect
def dont_logredirect():
	global logredirect_enable
	logredirect_enable = False


# don't debug by default
try:
	junk = debug_enable
except:
	debug_enable = False

# can be called from another script to enable debugging
def do_debug():
	global debug_enable
	debug_enable = True

# can be called from another script to disable debugging
def dont_debug():
	global debug_enable
	debug_enable = False


def out_raw(message):
	if logredirect_enable == True:
		klog_info(message)
	else:	
		sys.stdout.write(message);

def out(message):
	if logredirect_enable == True:
		klog_info(message)
	else:
		sys.stdout.write(message + "\n");

def err_raw(message):
	if logredirect_enable == True:
		klog_error(message)
	else:
		sys.stderr.write(message);

def err(message):
	if logredirect_enable == True:
		klog_error(message)
	else:
		sys.stderr.write(message + "\n");

def debug_raw(message, force=False):
	if debug_enable == True or force == True:
		if logredirect_enable == True:
			klog_debug(message)
		else:
			sys.stderr.write(message);

def debug(message, force=False):
	if debug_enable == True or force == True:
		if logredirect_enable == True:
			klog_debug(message)
		else:
			sys.stderr.write(message + "\n");


