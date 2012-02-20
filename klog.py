###
### LOGGING
###

import syslog
import sys

logname = sys.argv[0]

def klog_set_name(n):
	global logname
	logname = n

def klog_info(log):
	syslog.openlog(logname, 0, syslog.LOG_DAEMON)
	syslog.syslog(syslog.LOG_INFO, log)
	syslog.closelog()

def klog_error(log):
	syslog.openlog(logname, 0, syslog.LOG_DAEMON)
	syslog.syslog(syslog.LOG_ERR, log)
	syslog.closelog()

def klog_debug(log):
	syslog.openlog(logname, 0, syslog.LOG_DAEMON)
	syslog.syslog(syslog.LOG_DEBUG, log)
	syslog.closelog()



### TESTS ###

def klog_test():
	klog_info("info 1")
	klog_info("info 2")
	klog_error("error 1")
	klog_error("error 2")
	klog_debug("debug 1")
	klog_debug("debug 2")

if __name__ == "__main__":
	klog_test()

### /TESTS ###

