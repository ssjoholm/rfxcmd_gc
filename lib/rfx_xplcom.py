#!/usr/bin/python
# coding=UTF-8

# -----------------------------------------------------------------------------
#   
#   RFX_XPLCOM.PY
#   
#   Copyright (C) 2012-2013 Sebastian Sjoholm, sebastian.sjoholm@gmail.com
#   
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#   
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#   
#   Website
#   http://code.google.com/p/rfxcmd/
#
#   $Rev: 288 $
#   $Date: 2013-02-07 04:55:54 +0100 (Thu, 07 Feb 2013) $
#
# -----------------------------------------------------------------------------

import sys
import string
import select
import socket
import datetime

# -----------------------------------------------------------------------------

def send(host, message, sourcename = "rfxcmd-", hostname = True):
    """
    Send data to XPL network
    Credit: Jean-Louis Bergamo
    """

    sock = None
    addr = (host,3865)
	
    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    except socket.error as msg:
        sock = None

    try:
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
    except socket.error as msg:
        sock.close()
        sock = None

    if sock is None:
        print 'could not open socket'

	if hostname:
		sourcename = sourcename + socket.gethostname()
    
    #message = 'xpl-stat\n{\nhop=1\nsource=rfxcmd.'+hostname+'\ntarget=*\n}\nsensor.basic\n{\n' + message + '\n}\n' 
    message = 'xpl-stat\n{\nhop=1\nsource='+sourcename+'\ntarget=*\n}\nsensor.basic\n{\n' + message + '\n}\n' 
    sock.sendto(message,addr)
    sock.close()

# -----------------------------------------------------------------------------

def SendHeartbeat(port):
    """
    Send heartbeat
    Based on John Bent xPL Monitor for Python
    http://www.xplproject.org.uk/
    """
    sock = None
    
    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    except socket.error as msg:
        sock = None
        
    try:
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
    except socket.error as msg:
        sock.close()
        sock = None

    hostname = socket.gethostname()
    message = "xpl-stat\n{\nhop=1\nsource=xplmon."+hostname+"\ntarget=*\n}\nhbeat.app\n{\ninterval=5\nport=" + str(port) + "\n}\n"
    sock.sendto(message,("255.255.255.255",3865))

# -----------------------------------------------------------------------------

def listen():
    """
    Listen to xPL messages and print them to stdout with timestamps
    Based on John Bent xPL Monitor for Python
    http://www.xplproject.org.uk/
    """
    
    # Define maximum xPL message size
    buff = 1500

    port = 3865
    
    # Initialise the socket
    UDPSock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    addr = ("0.0.0.0",port)

    # Try and bind to the base port
    try:
        UDPSock.bind(addr)
    except:
        # A hub is running, so bind to a high port
        port = 50000

    addr = ("127.0.0.1",port)
    try:
        UDPSock.bind(addr)
    except:
        port += 1

    print "xPLMon, bound to port " + str(port) + ", exit with ctrl+c"

    SendHeartbeat(port)

    try:
        while 1==1:
            readable, writeable, errored = select.select([UDPSock],[],[],60)

            if len(readable) == 1:
                now = datetime.datetime.now()
                data,addr = UDPSock.recvfrom(buff)
                data = data.replace('\n', ' ')
                print now.strftime("%Y:%m:%d %H:%M:%S") + "\t" + data

    except KeyboardInterrupt:
        print "\nExit..."
        pass

if __name__ == '__main__':
	listen()
