#!/usr/bin/python
# coding=UTF-8

# ------------------------------------------------------------------------------
#	
#	RFXSEND.PY
#	
#	Copyright (C) 2012-2013 Sebastian Sjoholm, sebastian.sjoholm@gmail.com
#	
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#	
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#	
#	Website: http://code.google.com/p/rfxcmd/
#
#	$Rev: 566 $
#	$Date: 2013-11-22 21:43:41 +0100 (Fri, 22 Nov 2013) $
#
#	NOTES
#	
#	RFXCOM is a Trademark of RFSmartLink.
#
# ------------------------------------------------------------------------------
#
#                          Protocol License Agreement                      
#                                                                    
# The RFXtrx protocols are owned by RFXCOM, and are protected under applicable
# copyright laws.
#
# ==============================================================================
# It is only allowed to use this protocol or any part of it for RFXCOM products
# ==============================================================================
#
# The above Protocol License Agreement and the permission notice shall be 
# included in all software using the RFXtrx protocols.
#
# Any use in violation of the foregoing restrictions may subject the user to 
# criminal sanctions under applicable laws, as well as to civil liability for 
# the breach of the terms and conditions of this license.
#
# ------------------------------------------------------------------------------

__author__ = "Sebastian Sjoholm"
__copyright__ = "Copyright 2012-2013, Sebastian Sjoholm"
__license__ = "GPL"
__version__ = "0.1 (" + filter(str.isdigit, "$Rev: 566 $") + ")"
__maintainer__ = "Sebastian Sjoholm"
__email__ = "sebastian.sjoholm@gmail.com"
__status__ = "Development"
__date__ = "$Date: 2013-11-22 21:43:41 +0100 (Fri, 22 Nov 2013) $"

# Default modules
import sys
import string
import socket
import optparse

# ----------------------------------------------------------------------------

def ByteToHex( byteStr ):
	"""
	Convert a byte string to it's hex string representation e.g. for output.
	http://code.activestate.com/recipes/510399-byte-to-hex-and-hex-to-byte-string-conversion/

	Added str() to byteStr in case input data is in integer
	"""	
	return ''.join( [ "%02X " % ord( x ) for x in str(byteStr) ] ).strip()

# ----------------------------------------------------------------------------

def stripped(str):
	"""
	Strip all characters that are not valid
	Credit: http://rosettacode.org/wiki/Strip_control_codes_and_extended_characters_from_a_string
	"""
	return "".join([i for i in str if ord(i) in range(32, 127)])

# -----------------------------------------------------------------------------

def print_version():
	"""
	Print RFXSEND version, build and date
	"""
 	print "RFXSEND Version: " + __version__
 	print __date__.replace('$', '')
 	sys.exit(0)

# -----------------------------------------------------------------------------

def test_message( message ):
	"""
	Test, filter and verify that the incoming message is valid
	Return true if valid, False if not
	"""
		
	# Remove any whitespaces and linebreaks
	message = message.replace(' ', '')
	message = message.replace("\r","")
	message = message.replace("\n","")
	
	# Remove all invalid characters
	message = stripped(message)
	
	# Test the string if it is hex format
	try:
		int(message,16)
	except Exception:
		return False
	
	# Check that length is even
	if len(message) % 2:
		return False
	
	# Check that first byte is not 00
	if ByteToHex(message.decode('hex')[0]) == "00":
		return False
	
	# Length more than one byte
	if not len(message.decode('hex')) > 1:
		return False
	
	# Check if string is the length that it reports to be
	cmd_len = int( ByteToHex( message.decode('hex')[0]),16 )
	if not len(message.decode('hex')) == (cmd_len + 1):
		return False

	return True

# -----------------------------------------------------------------------------

def send_message(socket_server, socket_port, message):
	"""
	
	Send message to the RFXCMD socket server
	
	Input:
	- socket_server = IP address at RFXCMD
	- socket_port = socket port at RFXCMD
	- message = raw RFX message to be sent
	
	Output: None
	
	"""
	sock = None
	
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((socket_server, socket_port))
	sock.send(message)
	sock.close()
	
# -----------------------------------------------------------------------------

if __name__ == '__main__':

	parser = optparse.OptionParser()
	parser.add_option("-s", "--server", action="store", type="string", dest="server", help="IP address of the RFXCMD server (default: localhost)")
	parser.add_option("-p", "--port", action="store", type="string", dest="port", help="Port of the RFXCMD server (default: 55000)")
	parser.add_option("-r", "--rawcmd", action="store", type="string", dest="rawcmd", help="The raw message to be sent, multiple messages separated with comma")
	parser.add_option("-i", "--simulate", action="store_true", dest="simulate", help="Simulate send, nothing will be sent, instead printed on STDOUT")
	parser.add_option("-v", "--version", action="store_true", dest="version", help="Print rfxcmd version information")

	(options, args) = parser.parse_args()

	if options.version:
		print_version()

	if options.server:
		socket_server = options.server
	else:
		socket_server = 'localhost'

	if options.port:
		socket_port = int(options.port)
	else:
		socket_port = 55000
	
	if options.simulate:
		simulate = True
	else:
		simulate = False
	
	if options.rawcmd:
		message = options.rawcmd
		
		# check for multiple messages
		buf = message.split(',')
		
	else:
		print "Error: rawcmd message is missing"
		sys.exit(1)
	
	for msg in buf:
		if test_message(msg):
			try:
				if simulate == False:
					send_message(socket_server, socket_port, msg)
				else:
					print("Message to send, Server: " + str(socket_server) + ":" + str(socket_port) + ", Message: " + msg);
			except socket.error as err:
				print "Error: Could not send message: %s " % err
		else:
			print "Command not sent, invalid format"
		
	sys.exit(0)

# ------------------------------------------------------------------------------
# END
# ------------------------------------------------------------------------------
