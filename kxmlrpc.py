# This module contains code that implements a XML-RPC client/server.

from kbase import *
import SocketServer, SimpleXMLRPCServer, xmlrpclib, httplib, socket

# This class implements a XML-RPC server that binds to a UNIX socket. The path
# to the UNIX socket to create and the instance containing the user-defined RPC
# methods must be provided. The caller should call 'serve_forever()' to handle
# the RPC calls.
class UnixXmlRpcServer(SocketServer.UnixStreamServer, SimpleXMLRPCServer.SimpleXMLRPCDispatcher):
    def __init__(self, sock_path, instance, request_handler=SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):
	if os.path.exists(sock_path): os.unlink(sock_path)
    	self.logRequests = 0
    	SimpleXMLRPCServer.SimpleXMLRPCDispatcher.__init__(self, encoding=None, allow_none=1)
    	SocketServer.UnixStreamServer.__init__(self, sock_path, request_handler)
	self.register_instance(instance)

# This class implements a XML-RPC client that connects to a UNIX socket. The
# path to the UNIX socket to create must be provided. The RPC calls can be made
# directly from this object by calling the RPC methods by their name (i.e. as if
# they belonged to this object).
class UnixXmlRpcClient(xmlrpclib.ServerProxy):
    def __init__(self, sock_path):
    
        # We can't pass funny characters in the host part of a URL, so we encode
        # the socket path in hexadecimal.
	xmlrpclib.ServerProxy.__init__(self, 'http://' + str_to_hex(sock_path), transport=UnixXmlRpcTransport(),
	    	    	    	       allow_none=1)

# Helper classes for UnixXmlRpcClient.
class UnixXmlRpcTransport(xmlrpclib.Transport):
    def make_connection(self, host):
    	return UnixXmlRpcHttp(host)
	
class UnixXmlRpcHttpConn(httplib.HTTPConnection):
    def connect(self): 
    	self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    	self.sock.connect(hex_to_str(self.host))

class UnixXmlRpcHttp(httplib.HTTP):
    _connection_class = UnixXmlRpcHttpConn

# Exception being thrown when a RPC call fails.
XmlRpcFault = xmlrpclib.Fault

# This function converts a RPC call fault to a string.
def XmlRpcFaultToStr(fault):
    match = re.compile('.+:(.*)').match(fault.faultString)
    if match: return match.group(1)
    return fault.faultString
