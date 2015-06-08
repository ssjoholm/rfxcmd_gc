#!/usr/bin/python
# coding=UTF-8

# ------------------------------------------------------------------------------
#	
#	RFX_UTILS.PY
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
#	Version history can be found at 
#	http://code.google.com/p/rfxcmd/wiki/VersionHistory
#
#	$Rev: 464 $
#	$Date: 2013-05-01 22:41:36 +0200 (Wed, 01 May 2013) $
#
# ------------------------------------------------------------------------------

# --------------------------------------------------------------------------

def stripped(str):
	"""
	Strip all characters that are not valid
	Credit: http://rosettacode.org/wiki/Strip_control_codes_and_extended_characters_from_a_string
	"""
	return "".join([i for i in str if ord(i) in range(32, 127)])

# --------------------------------------------------------------------------

def ByteToHex( byteStr ):
	"""
	Convert a byte string to it's hex string representation e.g. for output.
	http://code.activestate.com/recipes/510399-byte-to-hex-and-hex-to-byte-string-conversion/

	Added str() to byteStr in case input data is in integer
	"""	
	return ''.join( [ "%02X " % ord( x ) for x in str(byteStr) ] ).strip()

# ----------------------------------------------------------------------------

def dec2bin(x, width=8):
	"""
	Base-2 (Binary) Representation Using Python
	http://stackoverflow.com/questions/187273/base-2-binary-representation-using-python
	Brian (http://stackoverflow.com/users/9493/brian)
	"""
	return ''.join(str((x>>i)&1) for i in xrange(width-1,-1,-1))

# ----------------------------------------------------------------------------

def testBit(int_type, offset):
	"""
	testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.
	http://wiki.python.org/moin/BitManipulation
	"""
	mask = 1 << offset
	return(int_type & mask)

# ----------------------------------------------------------------------------

def clearBit(int_type, offset):
	"""
	clearBit() returns an integer with the bit at 'offset' cleared.
	http://wiki.python.org/moin/BitManipulation
	"""
	mask = ~(1 << offset)
	return(int_type & mask)

# ----------------------------------------------------------------------------

def split_len(seq, length):
	"""
	Split string into specified chunks.
	"""
	return [seq[i:i+length] for i in range(0, len(seq), length)]

# ----------------------------------------------------------------------------
