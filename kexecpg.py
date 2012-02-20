#!/usr/bin/env python

# This program executes the list of SQL statements contained in the specified
# file.
# 
# The statements must be formatted in the same way as in a '.sql' file. The
# statements are not interpreted by psql(1), thus the commands of the form '\*'
# are not recognized.
# 
# If a line of the form '<<< * >>>' is encountered, special processing occurs.
# The program extracts the directives contained within the '<<<' and '>>>'
# delimiters and executes them sequentially until all directives have been
# executed or a stopping condition is reached. If a stopping condition is
# reached, the directives and the SQL statements that follow are skipped until
# the next '<<< * >>>' line is encountered.
#
# The directives are separated by commas. Example:
# <<< isset(create), isdb(kas), connect(kas), set(creating) >>>
#
# Accepted directives:
# isdb/istable/isrole/islang/isuser(name): skip block if 'name' is not a
#   database/table/role/language/user.
# isnodb/isnotable/isnorole/isnolang/isnouser(name): skip block if 'name' is a
#   database/table/role/language/user.
# isset(name): skip block if the specified command-line switch was not
#   specified.
# isnotset(name): skip block if the specified command-line switch was specified.
# set(name)/unset(name): set/unset the specified switch.
# createdb(name, encoding)/dropdb(name): create/drop database 'name', optionally
#   with the encoding specified.
# connect(name): connect to database 'name'.
# print(name): print 'name'.
# exit(name): print 'name' if specified and exit.

import getopt
from kpg import *
from kout import *

# Represent a directive.
class Directive(object):
    def __init__(self, name, arg_list, handler, line_nb):
        self.name = name
        self.arg_list = arg_list
        self.handler = handler
        self.line_nb = line_nb

# Represent a list of directives with its associated list of statements.
class FileBlock(object):
    def __init__(self, dir_text, dir_list, stmt, line_nb):
        self.dir_text = dir_text
        self.dir_list = dir_list
        self.stmt = stmt
        self.line_nb = line_nb

# Directive handlers.
def handle_is_in_table(dir, table_name, field_name):
    arg_name = dir.arg_list[0]
    cur = exec_pg_query(db, "SELECT %s FROM %s WHERE %s = %s" % \
                            (field_name, table_name, field_name, escape_pg_string(arg_name)))
    present = (cur.fetchone() != None)
    cur.close()
    if dir.name.startswith("isno"): return not present
    return present

def handle_isfield(dir):
    table_name = dir.arg_list[0]
    field_name = dir.arg_list[1]
    query = """
SELECT column_name FROM information_schema.columns
WHERE
  table_name = %s AND
  column_name = %s
""" % (escape_pg_string(table_name.strip()), escape_pg_string(field_name.strip()))
    cur = exec_pg_query(db, query)
    present = (cur.fetchone() != None)
    cur.close()
    if dir.name.startswith("isno"): return not present
    return present

def handle_istrigger(dir):
    trigger_name = dir.arg_list[0]
    trigger_table = dir.arg_list[1]
    trigger_type = dir.arg_list[2]
    query = """
SELECT trigger_name FROM information_schema.triggers 
WHERE 
  trigger_name = %s AND 
  event_manipulation = %s AND
  event_object_table = %s
""" % (escape_pg_string(trigger_name.strip()), escape_pg_string(trigger_type.strip().upper()), escape_pg_string(trigger_table.strip()))
    cur = exec_pg_query(db, query)
    present = (cur.fetchone() != None)
    cur.close()
    if dir.name.startswith("isno"): return not present
    return present

def handle_end(dir):
    return 1;

def handle_isdb(dir):
    return handle_is_in_table(dir, "pg_database", "datname")
    
def handle_istable(dir):
    return handle_is_in_table(dir, "pg_tables", "tablename")

def handle_isrole(dir):
    return handle_is_in_table(dir, "pg_roles", "rolname")

def handle_islang(dir):
    return handle_is_in_table(dir, "pg_language", "lanname")

def handle_isuser(dir):
    return handle_is_in_table(dir, "pg_user", "usename")

def handle_istype(dir):
    return handle_is_in_table(dir, "pg_type", "typname")

def handle_isindex(dir):
    return handle_is_in_table(dir, "pg_indexes", "indexname")

def handle_isset(dir):
    arg_name = dir.arg_list[0]
    present = switch_dict.has_key(arg_name)
    if dir.name == "isnotset": return not present
    return present

def handle_set(dir):
    arg_name = dir.arg_list[0]
    if dir.name == "set": switch_dict[arg_name] = arg_name
    elif switch_dict.has_key(arg_name): del switch_dict[arg_name]
    return 1
    
def handle_connect(dir):
    global db
    
    # Commit the current transaction.
    if no_act_flag == 0:
        db.commit()
    db.close()
    
    # Connect to the specified database.
    arg_name = dir.arg_list[0]
    db = open_pg_conn(arg_name, port = default_port)
    return 1

def handle_createdb(dir):
    if len(dir.arg_list) != 1 and len(dir.arg_list) != 2:
        raise Exception("invalid number of arguments for createdb at line " + str(dir.line_nb))
    
    arg_name = dir.arg_list[0]
    if dir.name == "createdb": cmd = "CREATE"
    else: cmd = "DROP"
    
    encoding = ""
    if len(dir.arg_list) == 2: encoding = " with encoding '%s'" % (dir.arg_list[1])
    
    # Commit the current transaction.
    if no_act_flag == 0:
        db.commit()
    
    query = "%s DATABASE %s%s" % (cmd, arg_name, encoding)
    if no_act_flag == 0:
        # Set autocommit to true temporarily to enable the creation/dropping of the
        # database.
        db.autocommit = 1
        exec_pg_query(db, query)
        db.autocommit = 0
    else:
        print query
    
    return 1

def handle_print(dir):
    arg_name = dir.arg_list[0]
    out(arg_name)
    return 1

def handle_exit(dir):

    # Commit the current transaction.
    if no_act_flag == 1:
        db.commit()
        db.close()
    
    if len(dir.arg_list): out(dir.arg_list[0])
    sys.exit(0)

# Parse the text specified containing a list of directives and return the list
# of directives.
def parse_directive_list_text(text, line_nb):
    dir_list = []
    text = text.strip()
    first = 1
    
    while len(text):
        if not first:
            if text.startswith(","): text = text[1:].strip()
            else: raise Exception("missing commit at line " + str(line_nb))
            
        first = 0
        match = re.compile("^(\w+)\(([^(]*?)\)").match(text)
        if not match: raise Exception("invalid format for directive line " + text + " at line " + str(line_nb))
        
        dir_name = match.group(1)
        dir_arg_text = match.group(2).strip()
        text = text[len(match.group(0)):].strip()
        
        arg_list = []
        if dir_arg_text != "":
            for arg in dir_arg_text.split(","):
                arg_list.append(arg)
        
        entry_found = None
        for entry in dir_dispatch_table:
            if entry[0] == dir_name:
                entry_found = entry
                break
         
        if not entry_found: raise Exception("unrecognized directive " + dir_name + " at line " + str(line_nb))
        if entry_found[1] != None and entry_found[1] != len(arg_list):
            raise Exception("unexpected number of arguments in directive " + dir_name + " at line " + str(line_nb))
        
        dir_list.append(Directive(dir_name, arg_list, entry_found[2], line_nb))
    
    return dir_list

# Get the list of blocks.
def get_block_list(file_path):
    block_list = []
    cur_dir_text = ""
    cur_dir_list = []
    cur_stmt = ""
    
    if file_path == "-": f = sys.stdin
    else: f = open(file_path, "rb")
    line_nb = 0
    
    for line in f.readlines():
        stripped_line = line.strip()
        line_nb += 1
        match = re.compile("<<<(.*)>>>").match(stripped_line)
        
        # File block.
        if match:
            if len(cur_dir_list) or len(cur_stmt):
                block_list.append(FileBlock(cur_dir_text, cur_dir_list, cur_stmt, line_nb))
            cur_dir_text = match.group(1)
            cur_stmt = ""
            cur_dir_list = parse_directive_list_text(cur_dir_text, line_nb)
        
        # Comment or empty line.
        elif len(stripped_line) == 0 or stripped_line.startswith("#") or stripped_line.startswith('--'):
            pass
        
        # Statement.
        else:
            if cur_stmt != "": cur_stmt += "\n"
            cur_stmt += line
    
    # Add the last block, if any.
    if len(cur_dir_list) or len(cur_stmt): block_list.append(FileBlock(cur_dir_text, cur_dir_list, cur_stmt, line_nb))
    
    f.close()
    return block_list

# Process the specified block.
def process_block(block):
    
    # Process the directives.
    if debug_flag: out("<<<" + block.dir_text + ">>>")
    
    ok_flag = 1
    for dir in block.dir_list:
        ok_flag = dir.handler(dir)
        if not ok_flag: break
    
    # Process the statements, if required.
    if ok_flag and len(block.stmt):
        if debug_flag: out(block.stmt)
        if no_act_flag == 0:
            cur = exec_pg_query(db, block.stmt)
            cur.close()
        else:
            print block.stmt

# Process the specified file.
def process_file(file_path):
    global db
    
    # Get the list of blocks.        
    block_list = get_block_list(file_path)
    
    # Open the connection to template1.
    if debug_flag: out("Connecting to database template1.")
    db = open_pg_conn("template1", port = default_port)
    
    # Process the blocks.
    for block in block_list: process_block(block)
    
    # Commit the transaction, if required.
    db.commit()
    db.close()

# Print the program usage.
def print_usage():
    s = "Usage: " + sys.argv[0] + " [options] <filename>\n" + \
        " Options:\n" + \
        " -h, --help                   show this message and exits\n" + \
        " -d, --debug                  print debugging information\n" + \
        " -s, --switch <name>          activate switch 'name'\n" + \
        " -n, --no-act                 don't act; output instructions\n" + \
        "\n" + \
        "If the file name is '-', the data is read from standard input.\n"
    out(s)

def main():
    global debug_flag
    global switch_dict
    global no_act_flag
    global default_port
    
    no_act_flag = 0
    debug_flag = 0
    switch_dict = {}
    default_port = 5432
    
    # Parse the command line.
    try: opts, args = getopt.getopt(sys.argv[1:], "nhds:p:", 
                                    ["help", "debug", "switch=", "no-act", "port="])
    except getopt.GetoptError, e:
	sys.stderr.write("Options error: '%s'\n" % (str(e)))
	print_usage()
	sys.exit(1)

    for k, v in opts:
	if k == "-d" or k == "--debug":
	    debug_flag = 1
        elif k == "-h" or k == "--help":
            print_usage()
            sys.exit(0)
        elif k == "-s" or k == "--switch":
            switch_dict[v] = v
        elif k == "-n" or k == "--no-act":
            no_act_flag = 1
        elif k == "-p" or k == "--port":
            default_port = int(v)
    
    if len(args) != 1:
	print_usage()
	sys.exit(1)
    
    try:
        if debug_flag: do_debug()
        process_file(args[0])
    except SystemExit: raise
    except Exception, e:
        err("Error: " + str(e) + ".")
        sys.exit(1)

# Directive dispatch table. The first column is the directive name, the second
# is the number of arguments, the third is the handler function to call. 'None'
# can be specified for the number of arguments when the command takes a variable
# number of arguments. The argument supplied to the handler is the directive
# itself. The handler must return true if the processing of the current block
# must continue.
dir_dispatch_table = (("isdb", 1, handle_isdb),
                      ("isnodb", 1, handle_isdb),
                      ("istable", 1, handle_istable),
                      ("isnotable", 1, handle_istable),
                      ("isrole", 1, handle_isrole),
                      ("isnorole", 1, handle_isrole),
                      ("islang", 1, handle_islang),
                      ("isnolang", 1, handle_islang),
                      ("isuser", 1, handle_isuser),
                      ("isnouser", 1, handle_isuser),
                      ("istype", 1, handle_istype),
                      ("isnotype", 1, handle_istype),
                      ("isindex", 2, handle_isindex),
                      ("isnoindex", 1, handle_isindex),
                      ("isset", 1, handle_isset),
                      ("isnotset", 1, handle_isset),
                      ("istrigger", 3, handle_istrigger),
                      ("isnotrigger", 3, handle_istrigger),
                      ("isfield", 2, handle_isfield),
                      ("isnofield", 2, handle_isfield),
                      ("end", None, handle_end),
                      ("set", 1, handle_set),
                      ("unset", 1, handle_set),
                      ("createdb", None, handle_createdb),
                      ("dropdb", 1, handle_createdb),
                      ("connect", 1, handle_connect),
                      ("print", 1, handle_print),
                      ("exit", None, handle_exit))

if __name__ == "__main__":
    main()

