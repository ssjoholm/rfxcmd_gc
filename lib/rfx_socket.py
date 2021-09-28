#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# ------------------------------------------------------------------------------
#
#    RFX_SOCKET.PY
#
#    Copyright (C) 2012-2013 Olivier Djian,
#                            Sebastian Sjoholm, sebastian.sjoholm@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Website: http://code.google.com/p/rfxcmd/
#
#    $Rev: 365 $
#    $Date: 2013-03-24 12:58:25 +0100 (Sun, 24 Mar 2013) $
#
# ------------------------------------------------------------------------------

__author__ = "Sebastian Sjoholm"
__copyright__ = "Copyright 2012-2014, Sebastian Sjoholm"
__license__ = "GPL"
__version__ = "2.0.0"
__maintainer__ = "Nicolas Béguier"
__date__ = "$Date: 2019-06-12 08:05:33 +0100 (Thu, 12 Jun 2019) $"

from logging import getLogger
from queue import Queue
from socketserver import TCPServer, StreamRequestHandler
from threading import Thread

LOGGER = getLogger('rfxcmd')
TCPServer.allow_reuse_address = True
MESSAGEQUEUE = Queue()

# ------------------------------------------------------------------------------

class NetRequestHandler(StreamRequestHandler):

    def handle(self):
        LOGGER.debug("Client connected to [%s:%d]" % self.client_address)
        lg = self.rfile.readline()
        MESSAGEQUEUE.put(lg)
        LOGGER.debug("Message read from socket: %s", lg.strip())

        self.net_adapter_client_connected = False
        LOGGER.info("Client disconnected from [%s:%d]" % self.client_address)

class RFXcmdSocketAdapter(StreamRequestHandler):
    def __init__(self, address='localhost', port=55000):
        self.address = address
        self.port = port
        self.net_adapter = TCPServer((self.address, self.port), NetRequestHandler)
        if self.net_adapter:
            self.net_adapter_registered = True
            Thread(target=self.loopNetServer, args=()).start()

    def loopNetServer(self):
        LOGGER.info("LoopNetServer Thread started")
        LOGGER.info("Listening on: [%s:%d]" % (self.address, self.port))
        self.net_adapter.serve_forever()
        LOGGER.info("LoopNetServer Thread stopped")

# ------------------------------------------------------------------------------
# END
# ------------------------------------------------------------------------------
