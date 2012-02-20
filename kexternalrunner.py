#!/usr/bin/env python

# infinite loop
# when <file> appears:
# - run <command> [params]
# - delete <file>
# - sleep 0.1 second

# bugs:
# - will "freeze" if called command does not exists

# TODO:
# - flags for redirect_to_log, debug, ...
# - timeout, kill -TERM, kill -9, ...


import os, sys, time, getopt

from krun import *

def usage():
    out("Usage:")
    out("       %s --help" % (sys.argv[0]))
    out("       %s [-d|--debug] [-r|--log-redirect] <file> <command> [params]" % (sys.argv[0]))

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "dr", ["debug", "log-redirect"])
    except getopt.GetoptError, e:
        sys.stderr.write("Options error: '%s'\n" % (str(e)) )
        usage()
        sys.exit(1)

    log_redirect_flag = False
    debug_flag = False

    for k, v in opts:
        if k == "-h" or k == "--help":
            usage()
            sys.exit(0)
        elif k == "-d" or k == "--debug":
            debug_flag = True
        elif k == "-r" or k == "--log-redirect":
            log_redirect_flag = True

    if debug_flag:
        do_debug()
    if log_redirect_flag:
        do_logredirect()

    if len(args) < 2:
        usage()
        sys.exit(1)

    file_path = args[0]
    command = args[1:]

    debug("file: %s" % (file_path))
    debug("command: %s" % (" ".join(command)))

    try:
        while 1:
            run = True

            try:
                #debug("loop")
                if run == True and os.path.exists(file_path):
                    run = False
                    out("Running command: '%s'" % (" ".join(command)))
                    proc = KPopen("", *command)
                    proc.debug_result()
                    os.remove(file_path)

            except KeyboardInterrupt:
                out("Exiting.")
                sys.exit(0)

            except Exception, e:
                out("Exception: '%s'" % (str(e)))

            time.sleep(0.1)

    except KeyboardInterrupt:
        out("Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()


