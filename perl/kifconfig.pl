#!/usr/bin/perl -w

# This program lists the network interfaces present on the machine. The format
# is the following:
# 
# 'Interface' <interface_name1> ':'
# <IP1> [ ':' <alias_id> ]
# <IP2> [ ':' <alias_id> ]
# ...
# 'Interface' <interface_name2> ':'
# <IP3> [ ':' <alias_id> ]
# <IP4> [ ':' <alias_id> ]
# ...
#
# Note that the module 'IfconfigWrapper.pm' (modified for Teambox) is required
# by this program.

use strict;
use Teambox::IfconfigWrapper;

my $info = IfconfigWrapper::Ifconfig('list', '', '', '') or die;

foreach my $iface_name (keys(%$info)) {
    my $iface = $info->{$iface_name};
    print("Interface $iface_name:\n");
    
    foreach my $inet_addr (keys(%{$iface->{'inet'}})) {
    	my $logic = $iface->{'logic'}{$inet_addr};
	print("$inet_addr");
	if ($logic ne '') { print(":$logic"); }
	print("\n");
    }
    
    print("\n");
}

