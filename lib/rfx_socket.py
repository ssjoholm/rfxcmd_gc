#!/usr/bin/python
# -*- coding:utf-8 -*-

# ------------------------------------------------------------------------------
#	
#	RFX_SOCKET.PY
#	
#	Copyright (C) 2012-2013 Olivier Djian,
#							Sebastian Sjoholm, sebastian.sjoholm@gmail.com
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
#	$Rev: 365 $
#	$Date: 2013-03-24 12:58:25 +0100 (Sun, 24 Mar 2013) $
#
# ------------------------------------------------------------------------------

import time
import logging
import threading

from Queue import Queue
messageQueue = Queue()

import SocketServer
SocketServer.TCPServer.allow_reuse_address = True
from SocketServer import (TCPServer, StreamRequestHandler)

# Import WEEWX extension
try:
	from lib.rfx_weewx import *
except ImportError:
	print "Error: module lib/weewx.py not found"
	sys.exit(1)

logger = logging.getLogger('rfxcmd')
	
# ------------------------------------------------------------------------------

class NetRequestHandler(StreamRequestHandler):
	
	def handle(self):
		logger.debug("Client connected to [%s:%d]" % self.client_address)
		lg = self.rfile.readline()
		messageQueue.put(lg)
		logger.debug("Message read from socket: " + lg.strip())
		
		# WEEWX incoming string
		if lg.strip() == '0A1100FF001100FF001100':
			logger.debug("WeeWx request, send data to WeeWx")
			try:
				self.wfile.write("Received request weewx weatherstation - ok\n")
				self.wfile.write(wwx.weewx_result() + '\n')
				self.wfile.write("Sent result - ok\n")
			except Exception, e:
				logger.debug("Error: WeeWx data send failed")
				logger.debug("Error: %s" % str(e))
				pass
		
		# WEEWX v2
		if lg[0:5] == "WEEWX":
			logger.debug("Process WeeWx request")
			indata = lg.split(';')
			logger.debug("Indata[0]: %s" % str(indata[0].strip()))
			logger.debug("Indata[1]: %s" % str(indata[1].strip()))
			
			# Sensor 0x4f
			if indata[1].strip() == "0x4f":
				logger.debug("Send WeeWx data for sensor 0x4f")
				self.wfile.write(wwx.weewx_0x4f())
			
			# Sensor 0x50
			if indata[1].strip() == "0x50":
				logger.debug("Send WeeWx data for sensor 0x50")
				self.wfile.write(wwx.weewx_0x50())
			
			# Sensor 0x51
			if indata[1].strip() == "0x51":
				logger.debug("Send WeeWx data for sensor 0x51")
				self.wfile.write(wwx.weewx_0x51())
			
			# Sensor 0x52
			if indata[1].strip() == "0x52":
				logger.debug("Send WeeWx data for sensor 0x52")
				self.wfile.write(wwx.weewx_0x52())
			
			# Sensor 0x53
			if indata[1].strip() == "0x53":
				logger.debug("Send WeeWx data for sensor 0x53")
				self.wfile.write(wwx.weewx_0x53())
			
			# Sensor 0x54
			if indata[1].strip() == "0x54":
				logger.debug("Send WeeWx data for sensor 0x54")
				self.wfile.write(wwx.weewx_0x54())
			
			# Sensor 0x55
			if indata[1].strip() == "0x55":
				logger.debug("Send WeeWx data for sensor 0x55")
				self.wfile.write(wwx.weewx_0x55())
			
			# Sensor 0x56
			if indata[1].strip() == "0x56":
				logger.debug("Send WeeWx data for sensor 0x56")
				self.wfile.write(wwx.weewx_0x56())
			
			# Sensor 0x57
			if indata[1].strip() == "0x57":
				logger.debug("Send WeeWx data for sensor 0x57")
				self.wfile.write(wwx.weewx_0x57())
		
		self.netAdapterClientConnected = False
		logger.info("Client disconnected from [%s:%d]" % self.client_address)
	
class RFXcmdSocketAdapter(object, StreamRequestHandler):
	def __init__(self, address='localhost', port=55000):
		self.Address = address
		self.Port = port

		self.netAdapter = TCPServer((self.Address, self.Port), NetRequestHandler)
		if self.netAdapter:
			self.netAdapterRegistered = True
			threading.Thread(target=self.loopNetServer, args=()).start()

	def loopNetServer(self):
		logger.info("LoopNetServer Thread started")
		logger.info("Listening on: [%s:%d]" % (self.Address, self.Port))
		self.netAdapter.serve_forever()
		logger.info("LoopNetServer Thread stopped")

# ------------------------------------------------------------------------------
# END
# ------------------------------------------------------------------------------
