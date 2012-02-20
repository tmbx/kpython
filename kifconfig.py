# This module is a wrapper around the program "kifconfig.pl" which lists the
# configured interfaces of the machine. It also contains methods to manipulate
# IP addresses.

from krun import *

# This function returns a dictionary indexed by the name of each interface and
# whose values are a list of objects having two fields, 'addr' and 'alias_id'.
def list_network_iface():
    cmd_output = get_cmd_output(['kifconfig.pl'])
    out = {}
    cur_iface = None
    
    for line in cmd_output.split("\n"):
	
	# Empty line. Reset current interface.
	if line == "":
	    cur_iface = None
	
	# New interface.
	elif re.match("^Interface", line):
	    match = re.compile('^Interface (.*):$').match(line)
	    if not match: raise Exception("cannot parse interface name")
	    name = match.group(1)
	    cur_iface = []
	    out[name] = cur_iface
	
	# Interface address.
	else:
	    if cur_iface == None: raise Exception("unexpected line " + line)
	    match = re.compile('^(.*?)(?:(?::(\d+)|))$').match(line)
	    addr = match.group(1)
	    alias_id = match.group(2)
	    cur_iface.append(Namespace(addr=addr, alias_id=alias_id))
    
    return out

# This function returns the address currently associated to the interface
# "eth0".
def get_current_server_address():
    d = list_network_iface()
    if not d.has_key("eth0"): return ""
    for el in d["eth0"]:
	if el.alias_id == None: return el.addr
    return ""

# This function parses the dotted IP address specified and returns it as an
# integer. This function and the functions below are adapted from the module
# inet.py.
def parse_dotted_ip(ip):
    bytes = string.split(ip, ".")
    if len(bytes) != 4: raise ValueError("invalid IP address " + ip)
    for byte in bytes:
	    if int(byte) > 255: raise ValueError("invalid IP address " + ip)
    return (int(bytes[0]) << 24) + (int(bytes[1]) << 16) + (int(bytes[2]) << 8) + (int(bytes[3])) 
	
# This function converts an integer IP address to the dotted notation.
def numeric_ip_to_dotted(ip):
    return "%u.%u.%u.%u" % ((ip >> 24), ((ip & 0xff0000) >> 16), ((ip & 0xff00) >> 8), (ip & 0xff))

# This function computes the network mask of the given dotted IP address.
def compute_ip_netmask(ip):
    num_ip = parse_dotted_ip(ip)
    if num_ip & 0x80000000 == 0: return numeric_ip_to_dotted(0xff000000)
    if num_ip & 0x40000000 == 0: return numeric_ip_to_dotted(0xffff0000)
    return numeric_ip_to_dotted(0xffff0000)

