#!/usr/bin/python
# coding=UTF-8

# ------------------------------------------------------------------------------
#
#   RFXCMD.PY
#
#   Copyright (C) 2012-2014 Sebastian Sjoholm, sebastian.sjoholm@gmail.com
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
#   along with this program.  If not, see <http://www.gnu.org/licenses/>
#
#   Version history can be found at
#   http://code.google.com/p/rfxcmd/wiki/VersionHistory
#
#   NOTES
#
#   RFXCOM is a Trademark of RFSmartLink.
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
__copyright__ = "Copyright 2012-2014, Sebastian Sjoholm"
__license__ = "GPL"
__version__ = "0.4"
__maintainer__ = "Nicolas Béguier"
__date__ = "$Date: 2018-12-27 14:05:33 +0100 (Thu, 27 Dec 2018) $"

# Default modules
from inspect import currentframe, getframeinfo
from json import dumps
from logging import Formatter, StreamHandler, getLogger, getLevelName, FileHandler
from optparse import OptionParser
import os
from time import strftime, sleep
from traceback import format_exc
from re import match
from signal import signal, SIGINT, SIGTERM
from string import whitespace
import sys
import xml.dom.minidom as minidom

# 3rd party modules
# These might not be needed, depended on usage
from serial import Serial, VERSION, SerialException

# Debug
# from pdb import set_trace as st

# RFXCMD modules
from lib.rfx_socket import MESSAGEQUEUE, RFXcmdSocketAdapter
from lib.rfx_command import Command
from lib.rfx_utils import stripped, ByteToHex, dec2bin, testBit, clearBit
import lib.rfx_sensors
import lib.rfx_decode as rfxdecode
import lib.rfx_protocols as protocol

# ------------------------------------------------------------------------------
# VARIABLE CLASSS
# ------------------------------------------------------------------------------

class ConfigData:
    def __init__(
            self,
            serial_active=True,
            serial_device=None,
            serial_rate=38400,
            serial_timeout=9,
            trigger_active=False,
            trigger_onematch=False,
            trigger_file="",
            trigger_timeout=10,
            loglevel="info",
            logfile="rfxcmd.log",
            program_path="",
            socketserver=False,
            sockethost="",
            socketport="",
            whitelist_active=False,
            whitelist_file="",
            daemon_active=False,
            daemon_pidfile="rfxcmd.pid",
            process_rfxmsg=True,
            barometric=0,
            log_msg=False,
            log_msgfile="",
            protocol_startup=False,
            protocol_file="protocol.xml"
        ):

        self.serial_active = serial_active
        self.serial_device = serial_device
        self.serial_rate = serial_rate
        self.serial_timeout = serial_timeout
        self.trigger_active = trigger_active
        self.trigger_onematch = trigger_onematch
        self.trigger_file = trigger_file
        self.trigger_timeout = trigger_timeout
        self.loglevel = loglevel
        self.logfile = logfile
        self.program_path = program_path
        self.socketserver = socketserver
        self.sockethost = sockethost
        self.socketport = socketport
        self.whitelist_active = whitelist_active
        self.whitelist_file = whitelist_file
        self.daemon_active = daemon_active
        self.daemon_pidfile = daemon_pidfile
        self.process_rfxmsg = process_rfxmsg
        self.barometric = barometric
        self.log_msg = log_msg
        self.log_msgfile = log_msgfile
        self.protocol_startup = protocol_startup
        self.protocol_file = protocol_file

class CmdArgData:
    def __init__(
            self,
            configfile="",
            action="",
            rawcmd="",
            device="",
            createpid=False,
            pidfile="",
            printout_complete=True,
            printout_csv=False
        ):

        self.configfile = configfile
        self.action = action
        self.rawcmd = rawcmd
        self.device = device
        self.createpid = createpid
        self.pidfile = pidfile
        self.printout_complete = printout_complete
        self.printout_csv = printout_csv

class RfxCmdData:
    def __init__(
            self,
            reset="0d00000000000000000000000000",
            status="0d00000002000000000000000000",
            save="0d00000006000000000000000000"
        ):

        self.reset = reset
        self.status = status
        self.save = save

class SerialData:
    def __init__(
            self,
            port=None,
            rate=38400,
            timeout=9
        ):

        self.port = port
        self.rate = rate
        self.timeout = timeout

# Store the trigger data from xml file
class TriggerData:
    def __init__(
            self,
            data=""
        ):

        self.data = data

# Store the whitelist data from xml file
class WhitelistData:
    def __init__(
            self,
            data=""
        ):

        self.data = data

# ----------------------------------------------------------------------------
# DEAMONIZE
# Credit: George Henze
# ----------------------------------------------------------------------------

def shutdown():
    """
    Shutdown function
    """
    # clean up PID file after us
    log_me('debug', "Shutdown")

    if cmdarg.createpid:
        log_me('debug', "Removing PID file " + str(cmdarg.pidfile))
        os.remove(cmdarg.pidfile)

    if serial_param.port is not None:
        log_me('debug', "Close serial port")
        serial_param.port.close()
        serial_param.port = None

    log_me('debug', "Exit 0")
    sys.stdout.flush()
    os._exit(0)

def handler(signum=None, frame=None):
    """
    Handler, signum & frame are used
    """
    if not isinstance(signum, type(None)):
        log_me('debug', "Signal %i caught, exiting..." % int(signum))
        shutdown()

def daemonize():
    try:
        pid = os.fork()
        if pid != 0:
            exit(0)
    except OSError, err:
        raise RuntimeError("1st fork failed: %s [%d]" % (err.strerror, err.errno))

    os.setsid()

    prev = os.umask(0)
    os.umask(prev and int('077', 8))

    try:
        pid = os.fork()
        if pid != 0:
            exit(0)
    except OSError, err:
        raise RuntimeError("2nd fork failed: %s [%d]" % (err.strerror, err.errno))

    dev_null = file('/dev/null', 'r')
    os.dup2(dev_null.fileno(), sys.stdin.fileno())

    if cmdarg.createpid:
        pid = str(os.getpid())
        log_me('debug', "Writing PID " + pid + " to " + str(cmdarg.pidfile))
        file(cmdarg.pidfile, 'w').write("%s\n" % pid)

# ----------------------------------------------------------------------------
# C __LINE__ equivalent in Python by Elf Sternberg
# http://www.elfsternberg.com/2008/09/23/c-__line__-equivalent-in-python/
# ----------------------------------------------------------------------------

def _line():
    info = getframeinfo(currentframe().f_back)[0:3]
    return '[%s:%d]' % (info[2], info[1])

# ----------------------------------------------------------------------------

def readbytes(number):
    """
    Read x amount of bytes from serial port.
    Credit: Boris Smus http://smus.com
    """
    buf = ''
    for _ in range(number):
        try:
            byte = serial_param.port.read()
        except IOError, err:
            log_me('error', err)
        except OSError, err:
            log_me('error', err)
        buf += byte

    return buf

# ----------------------------------------------------------------------------

def decode_packet(message):
    """
    Decode incoming RFXtrx message.
    """

    timestamp = strftime('%Y-%m-%d %H:%M:%S')
    decoded = False

    # Verify incoming message
    log_me('debug', "Verify incoming packet")
    if not test_rfx(ByteToHex(message)):
        log_me('error', "The incoming message is invalid (" +
               ByteToHex(message) + ") Line: " + _line())
        return
    else:
        log_me('debug', "Verified OK")

    raw_message = ByteToHex(message)
    raw_message = raw_message.replace(' ', '')

    packettype = ByteToHex(message[1])
    log_me('debug', "PacketType: %s" % str(packettype))

    if len(message) > 2:
        subtype = ByteToHex(message[2])
        log_me('debug', "SubType: %s" % str(subtype))

    if len(message) > 3:
        seqnbr = ByteToHex(message[3])
        log_me('debug', "SeqNbr: %s" % str(seqnbr))

    if len(message) > 4:
        id1 = ByteToHex(message[4])
        log_me('debug', "Id1: %s" % str(id1))

    if len(message) > 5:
        id2 = ByteToHex(message[5])
        log_me('debug', "Id2: %s" % str(id2))

    log_me('info', "Packettype\t\t\t= " + rfx.rfx_packettype[packettype])

    # ---------------------------------------
    # Verify correct length on packets
    # ---------------------------------------
    log_me('debug', "Verify correct packet length")
    if packettype == '00' and len(message) != 14:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '01' and len(message) != 14 and len(message) != 21:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '02' and len(message) != 5:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '10' and len(message) != 8:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '11' and len(message) != 12:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '12' and len(message) != 9:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '13' and len(message) != 10:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '15' and len(message) != 12:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '16' and len(message) != 8:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '17' and len(message) != 8:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '18' and len(message) != 8:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '19' and len(message) != 10:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '1A' and len(message) != 13:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '20' and len(message) != 9:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '28' and len(message) != 7:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '30' and len(message) != 7:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '40' and len(message) != 10:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '41' and len(message) != 7:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '42' and len(message) != 9:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '4E' and len(message) != 11:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '4F' and len(message) != 11:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '50' and len(message) != 9:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '51' and len(message) != 9:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '52' and len(message) != 11:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '53' and len(message) != 10:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '54' and len(message) != 14:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '55' and len(message) != 12:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '56' and len(message) != 17:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '57' and len(message) != 10:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '58' and len(message) != 14:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '59' and len(message) != 14:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '5A' and len(message) != 18:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '5B' and len(message) != 20:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '5C' and len(message) != 16:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '5D' and len(message) != 9:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '70' and len(message) != 8:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '71' and len(message) != 11:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '72' and len(message) != 10:
        log_me('error', "Packet has wrong length, discarding")
        decoded = True
        packettype = None

    # ---------------------------------------
    # If packet is OK and the log_msg is active
    # then save the packet to log_msgfile designated
    # file on disk
    # ---------------------------------------
    if not decoded and config.log_msg:
        log_me('debug', "Save packet to log_msgfile")
        try:
            data = str(ByteToHex(message))
            data = data.replace(' ', '')
            config_file = open(config.log_msgfile, "a+")
            config_file.write(data + "\n")
            config_file.close()
        except Exception, err:
            log_me('error', "Error when trying to write message log")
            log_me('error', err)

    # ---------------------------------------
    # 0x0 - Interface Control
    # ---------------------------------------
    if packettype == '00':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

    # ---------------------------------------
    # 0x01 - Interface Message
    # ---------------------------------------
    if packettype == '01':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        data = {
            'packetlen' : ByteToHex(message[0]),
            'packettype' : ByteToHex(message[1]),
            'subtype' : ByteToHex(message[2]),
            'seqnbr' : ByteToHex(message[3]),
            'cmnd' : ByteToHex(message[4]),
            'msg1' : ByteToHex(message[5]),
            'msg2' : ByteToHex(message[6]),
            'msg3' : ByteToHex(message[7]),
            'msg4' : ByteToHex(message[8]),
            'msg5' : ByteToHex(message[9]),
            'msg6' : ByteToHex(message[10]),
            'msg7' : ByteToHex(message[11]),
            'msg8' : ByteToHex(message[12]),
            'msg9' : ByteToHex(message[13])
        }

        # Subtype
        if data['subtype'] == '00':
            log_me('info', "Subtype\t\t\t= Interface response")
        else:
            log_me('info', "Subtype\t\t\t= Unknown type (" + data['packettype'] + ")")

        # Seq
        log_me('info', "Sequence nbr\t\t= " + data['seqnbr'])

        # Command
        try:
            log_me('info', "Response on cmnd\t= " + rfx.rfx_cmnd[data['cmnd']])
        except KeyError:
            log_me('warning', "Response on cmnd\t= Invalid")

        # MSG 1
        log_me('info', "Transceiver type\t= " + rfx.rfx_subtype_01_msg1[data['msg1']])

        # MSG 2
        log_me('info', "Firmware version\t= " + str(int(data['msg2'], 16)))

        log_me('info', "Protocols:")

        # ------------------------------------------------------
        # MSG 3

        protocol = str(rfx.rfx_subtype_01_msg3['128'])
        if testBit(int(data['msg3'], 16), 7) == 128:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg3['64'])
        if testBit(int(data['msg3'], 16), 6) == 64:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg3['32'])
        if testBit(int(data['msg3'], 16), 5) == 32:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg3['16'])
        if testBit(int(data['msg3'], 16), 4) == 16:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg3['8'])
        if testBit(int(data['msg3'], 16), 3) == 8:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg3['4'])
        if testBit(int(data['msg3'], 16), 2) == 4:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg3['2'])
        if testBit(int(data['msg3'], 16), 1) == 2:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg3['1'])
        if testBit(int(data['msg3'], 16), 0) == 1:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        # ------------------------------------------------------
        # MSG 4

        protocol = str(rfx.rfx_subtype_01_msg4['128'])
        if testBit(int(data['msg4'], 16), 7) == 128:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg4['64'])
        if testBit(int(data['msg4'], 16), 6) == 64:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg4['32'])
        if testBit(int(data['msg4'], 16), 5) == 32:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg4['16'])
        if testBit(int(data['msg4'], 16), 4) == 16:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg4['8'])
        if testBit(int(data['msg4'], 16), 3) == 8:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg4['4'])
        if testBit(int(data['msg4'], 16), 2) == 4:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg4['2'])
        if testBit(int(data['msg4'], 16), 1) == 2:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg4['1'])
        if testBit(int(data['msg4'], 16), 0) == 1:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        # ------------------------------------------------------
        # MSG 5

        protocol = str(rfx.rfx_subtype_01_msg5['128'])
        if testBit(int(data['msg5'], 16), 7) == 128:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg5['64'])
        if testBit(int(data['msg5'], 16), 6) == 64:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg5['32'])
        if testBit(int(data['msg5'], 16), 5) == 32:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg5['16'])
        if testBit(int(data['msg5'], 16), 4) == 16:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg5['8'])
        if testBit(int(data['msg5'], 16), 3) == 8:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg5['4'])
        if testBit(int(data['msg5'], 16), 2) == 4:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg5['2'])
        if testBit(int(data['msg5'], 16), 1) == 2:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        protocol = str(rfx.rfx_subtype_01_msg5['1'])
        if testBit(int(data['msg5'], 16), 0) == 1:
            log_me('info', "%-25s Enabled" % protocol)
        else:
            log_me('info', "%-25s Disabled" % protocol)

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x02 - Receiver/Transmitter Message
    # ---------------------------------------
    if packettype == '02':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")

        decoded = True

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_02[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)

        if subtype == '01':
            log_me('info', "Message\t\t\t= " + rfx.rfx_subtype_02_msg1[id1])

        # OUTPUT
        if subtype == '00':
            output_me(timestamp, message, packettype, subtype, seqnbr, [])
        else:
            output_me(timestamp, message, packettype, subtype, seqnbr, [('id1', id1)])

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x03 - Undecoded Message
    # ---------------------------------------
    if packettype == '03':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        indata = ByteToHex(message)

        # remove all spaces
        for i in whitespace:
            indata = indata.replace(i, "")

        indata = indata[4:]

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_03[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Message\t\t\t= " + indata)

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [('message', indata)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$message$", indata)
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x10 Lighting1
    # ---------------------------------------
    if packettype == '10':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")

        decoded = True

        # DATA
        try:
            housecode = rfx.rfx_subtype_10_housecode[ByteToHex(message[4])]
        except Exception as err:
            housecode = '0x' + housecode
            log_me('error', "Unknown house command received, %s" % str(err))

        unitcode = int(ByteToHex(message[5]), 16)
        try:
            command = rfx.rfx_subtype_10_cmnd[ByteToHex(message[6])]
        except Exception as err:
            command = '0x' + command
            log_me('error', "Unknown command received, %s" % str(err))

        signal = rfxdecode.decode_signal(message[7])

        try:
            display_subtype = str(rfx.rfx_subtype_10[subtype])
        except Exception as err:
            display_subtype = '0x' + subtype
            log_me('error', "Unknown subtype received, %s" % str(err))

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= %s" % display_subtype)
        log_me('info', "Seqnbr\t\t\t= %s" % str(seqnbr))
        log_me('info', "Housecode\t\t= %s" % str(housecode))
        log_me('info', "Unitcode\t\t= %s" % str(unitcode))
        log_me('info', "Command\t\t\t= %s" % str(command))
        log_me('info', "Signal level\t\t= %s" % str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, display_subtype, seqnbr, [
            ('signal_level', signal),
            ('housecode', housecode),
            ('command', command),
            ('unitcode', unitcode)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$housecode$", str(housecode))
                    action = action.replace("$unitcode$", str(unitcode))
                    action = action.replace("$command$", command)
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x11 Lighting2
    # ---------------------------------------
    if packettype == '11':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = ByteToHex(message[4]) + ByteToHex(message[5]) + \
            ByteToHex(message[6]) + ByteToHex(message[7])
        unitcode = int(ByteToHex(message[8]), 16)
        command = rfx.rfx_subtype_11_cmnd[ByteToHex(message[9])]
        dimlevel = rfx.rfx_subtype_11_dimlevel[ByteToHex(message[10])]
        signal = rfxdecode.decode_signal(message[11])

        try:
            display_subtype = str(rfx.rfx_subtype_11[subtype])
        except Exception as err:
            display_subtype = '0x' + subtype
            log_me('error', "Unknown subtype received, %s" % str(err))

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + display_subtype)
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + sensor_id)
        log_me('info', "Unitcode\t\t= " + str(unitcode))
        log_me('info', "Command\t\t\t= " + command)
        log_me('info', "Dim level\t\t= " + dimlevel + "%")
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, display_subtype, seqnbr, [
            ('signal_level', signal),
            ('id', sensor_id),
            ('command', command),
            ('unitcode', unitcode),
            ('dim_level', dimlevel)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$unitcode$", str(unitcode))
                    action = action.replace("$command$", command)
                    action = action.replace("$dimlevel$", dimlevel)
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x12 Lighting3
    # ---------------------------------------
    if packettype == '12':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        system = ByteToHex(message[4])

        if testBit(int(ByteToHex(message[5]), 16), 0) == 1:
            channel = 1
        elif testBit(int(ByteToHex(message[5]), 16), 1) == 2:
            channel = 2
        elif testBit(int(ByteToHex(message[5]), 16), 2) == 4:
            channel = 3
        elif testBit(int(ByteToHex(message[5]), 16), 3) == 8:
            channel = 4
        elif testBit(int(ByteToHex(message[5]), 16), 4) == 16:
            channel = 5
        elif testBit(int(ByteToHex(message[5]), 16), 5) == 32:
            channel = 6
        elif testBit(int(ByteToHex(message[5]), 16), 6) == 64:
            channel = 7
        elif testBit(int(ByteToHex(message[5]), 16), 7) == 128:
            channel = 8
        elif testBit(int(ByteToHex(message[6]), 16), 0) == 1:
            channel = 9
        elif testBit(int(ByteToHex(message[6]), 16), 1) == 2:
            channel = 10
        else:
            channel = 255

        command = rfx.rfx_subtype_12_cmnd[ByteToHex(message[7])]
        battery = rfxdecode.decode_battery(message[8])
        signal = rfxdecode.decode_signal(message[8])

        try:
            display_subtype = str(rfx.rfx_subtype_12[subtype])
        except Exception as err:
            display_subtype = '0x' + subtype
            log_me('error', "Unknown subtype received, %s" % str(err))

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + display_subtype)
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "System\t\t\t= " + system)
        log_me('info', "Channel\t\t\t= " + str(channel))
        log_me('info', "Command\t\t\t= " + command)
        log_me('info', "Battery\t\t\t= " + str(battery))
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, display_subtype, seqnbr, [
            ('battery', battery),
            ('signal', signal),
            ('system', system),
            ('command', command),
            ('channel', channel)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$system$", str(system))
                    action = action.replace("$channel$", str(channel))
                    action = action.replace("$command$", command)
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x13 Lighting4
    # ---------------------------------------
    if packettype == '13':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        code = ByteToHex(message[4]) + ByteToHex(message[5]) + ByteToHex(message[6])
        code1 = dec2bin(int(ByteToHex(message[4]), 16))
        code2 = dec2bin(int(ByteToHex(message[5]), 16))
        code3 = dec2bin(int(ByteToHex(message[6]), 16))
        code_bin = code1 + " " + code2 + " " + code3
        pulse = ((int(ByteToHex(message[7]), 16) * 256) + int(ByteToHex(message[8]), 16))
        signal = rfxdecode.decode_signal(message[9])

        try:
            display_subtype = str(rfx.rfx_subtype_13[subtype])
        except Exception as err:
            display_subtype = '0x' + subtype
            log_me('error', "Unknown subtype received, %s" % str(err))

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + display_subtype)
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Code\t\t\t= " + code)
        log_me('info', "S1-S24\t\t\t= "  + code_bin)
        log_me('info', "Pulse\t\t\t= " + str(pulse) + " usec")
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, display_subtype, seqnbr, [
            ('code', code),
            ('s1_s24', code_bin),
            ('pulse', pulse),
            ('pulse_usec', signal)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$code$", code_bin)
                    action = action.replace("$pulse$", str(pulse))
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x14 Lighting5
    # ---------------------------------------
    if packettype == '14':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2 + ByteToHex(message[6])
        unitcode = int(ByteToHex(message[7]), 16)

        if subtype == '00':
            command = rfx.rfx_subtype_14_cmnd0[ByteToHex(message[8])]
        elif subtype == '01':
            command = rfx.rfx_subtype_14_cmnd1[ByteToHex(message[8])]
        elif subtype == '02':
            command = rfx.rfx_subtype_14_cmnd2[ByteToHex(message[8])]
        elif subtype == '03':
            command = rfx.rfx_subtype_14_cmnd3[ByteToHex(message[8])]
        elif subtype == '04':
            command = rfx.rfx_subtype_14_cmnd4[ByteToHex(message[8])]
        elif subtype == '05':
            command = rfx.rfx_subtype_14_cmnd5[ByteToHex(message[8])]
        elif subtype == '06':
            try:
                command = rfx.rfx_subtype_14_cmnd5[ByteToHex(message[8])]
            except Exception as err:
                # if the value is between x06 and x84 it is 'select color'
                # This should be improved, as it will not catch unknown values
                log_me('error', "Value is not in the sensor list")
                command = "Select Color"

        else:
            command = "Unknown"

        if subtype == "00":
            level = ByteToHex(message[9])
        else:
            level = 0

        signal = rfxdecode.decode_signal(message[10])

        try:
            display_subtype = rfx.rfx_subtype_14[subtype]
        except Exception as err:
            log_me('error', "Invalid subtype")
            display_subtype = '0x' + subtype

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= %s" % display_subtype)
        log_me('info', "Seqnbr\t\t\t= %s" % str(seqnbr))
        log_me('info', "Id\t\t\t= %s" % str(sensor_id))

        if subtype != '03' and subtype != '05':
            log_me('info', "Unitcode\t\t= Not used")
            unitcode = 0
        else:
            log_me('info', "Unitcode\t\t= " + str(unitcode))

        log_me('info', "Command\t\t\t= " + command)

        if subtype == '00':
            log_me('info', "Level\t\t\t= " + level)

        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        if subtype == '00':
            output_me(timestamp, message, packettype, display_subtype, seqnbr, [
                ('id', sensor_id),
                ('unitcode', unitcode),
                ('command', command),
                ('level', level),
                ('signal_level', signal)])
        else:
            output_me(timestamp, message, packettype, display_subtype, seqnbr, [
                ('id', sensor_id),
                ('unitcode', unitcode),
                ('command', command),
                ('signal_level', signal)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$unitcode$", str(unitcode))
                    action = action.replace("$command$", command)
                    if subtype == '00':
                        action = action.replace("$level$", level)
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x15 Lighting6
    # Credit: Dimitri Clatot
    # ---------------------------------------
    if packettype == '15':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        groupcode = rfx.rfx_subtype_15_groupcode[ByteToHex(message[6])]
        unitcode = int(ByteToHex(message[7]), 16)
        command = rfx.rfx_subtype_15_cmnd[ByteToHex(message[8])]
        command_seqnbr = ByteToHex(message[9])
        seqnbr2 = ByteToHex(message[10])
        signal = rfxdecode.decode_signal(message[11])

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_15[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "ID\t\t\t= "  + sensor_id)
        log_me('info', "Groupcode\t\t= " + groupcode)
        log_me('info', "Unitcode\t\t= " + str(unitcode))
        log_me('info', "Command\t\t\t= " + command)
        log_me('info', "Command seqnbr\t\t= " + command_seqnbr)
        log_me('info', "Seqnbr2\t\t\t= %s" % str(seqnbr2))
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [
            ('id', sensor_id),
            ('signal_level', signal),
            ('groupcode', groupcode),
            ('command', command),
            ('unitcode', unitcode),
            ('command_seqnbr', command_seqnbr)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$groupcode$", groupcode)
                    action = action.replace("$unitcode$", str(unitcode))
                    action = action.replace("$command$", command)
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # --------------------------------------------------------------------------
    # 0x16 Chime
    # --------------------------------------------------------------------------
    if packettype == "16":
        log_me('debug', "Decode packetType 0x%s - Start" % str(packettype))
        decoded = True

        # DATA
        sensor_id = id1 + id2

        if subtype == "00":
            try:
                sound = rfx.rfx_subtype_16_sound[ByteToHex(message[6])]
            except Exception as err:
                log_me('error', err)
                sound = "Unknown"

        elif subtype == "01":
            sound = str(ByteToHex(message[6]))

        elif subtype == "02" or subtype == "03" or subtype == "04":
            sound = None

        try:
            signal = rfxdecode.decode_signal(message[7])
        except Exception as err:
            log_me('error', err)
            signal = "Error"

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= %s" % str(rfx.rfx_subtype_16[subtype]))
        log_me('info', "Seqnbr\t\t\t= %s" % str(seqnbr))
        log_me('info', "ID\t\t\t= %s" % str(sensor_id))
        if sound != None:
            log_me('info', "Sound\t\t\t= %s" % str(sound))
        log_me('info', "Signal level\t\t= %s" % str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [
            ('id', sensor_id),
            ('signal_level', signal)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: %s, Action: %s" % (str(trigger_message), str(action)))
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    if sound != None:
                        action = action.replace("$sound$", sound)
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x%s - End" % packettype)


    # ---------------------------------------
    # 0x17 Fan (Transmitter only)
    # ---------------------------------------
    if packettype == '17':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_18[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('warning', "This sensor is not completed.")

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x18 Curtain1 (Transmitter only)
    # ---------------------------------------
    if packettype == '18':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_18[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('warning', "This sensor is not completed.")

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x19 Blinds1
    # ---------------------------------------
    if packettype == '19':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")

        decoded = True

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_19[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('warning', "This sensor is not completed.")

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x1A RTS
    # ---------------------------------------
    if packettype == '1A':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2 + ByteToHex(message[6])

        try:
            subtype_str = rfx.rfx_subtype_1A[subtype]
        except Exception as err:
            log_me('error', "Unknown subtype")
            subtype = "Unknown subtype"

        if subtype == "00":
            unitcode = ByteToHex(message[6])
            if unitcode == "00":
                unitcode_str = "All"
            else:
                unitcode_str = str(unitcode)
        elif subtype == "01":
            unitcode = ByteToHex(message[6])
            unitcode_str = str(unitcode)

        command = ByteToHex(message[7])
        try:
            command_str = rfx.rfx_subtype_1A_cmnd[command]
        except Exception as err:
            log_me('error', "Unknown command received")
            command_str = "Unknown command received"

        signal = rfxdecode.decode_signal(message[8])

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= %s" % str(subtype_str))
        log_me('info', "Seqnbr\t\t\t= %s" % str(seqnbr))
        log_me('info', "Id1-3\t\t\t= %s" % str(sensor_id))
        log_me('info', "Unitcode\t\t= %s" % unitcode_str)
        log_me('info', "Command\t\t\t= %s" % command_str)
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [
            ('signal_level', signal),
            ('id', sensor_id),
            ('unicode', unitcode_str),
            ('command', command_str)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", str(subtype))
                    action = action.replace("$unitcode$", str(unitcode))
                    action = action.replace("$command$", str(command))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x20 Security1
    # Credit: Dimitri Clatot
    # ---------------------------------------
    if packettype == '20':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2 + ByteToHex(message[6])
        status = rfx.rfx_subtype_20_status[ByteToHex(message[7])]
        signal = rfxdecode.decode_signal(message[8])
        battery = rfxdecode.decode_battery(message[8])
        try:
            display_subtype = rfx.rfx_subtype_20[subtype]
        except KeyError:
            display_subtype = '0x' + subtype

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + display_subtype)
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t\t= " + sensor_id)
        log_me('info', "Status\t\t\t= " + status)
        log_me('info', "Battery\t\t\t= " + str(battery))
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, display_subtype, seqnbr, [
            ('battery', battery),
            ('signal_level', signal),
            ('id', sensor_id),
            ('status', status)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$status$", status)
                    action = action.replace("$battery$", str(battery))
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x28 Camera1
    # ---------------------------------------
    if packettype == '28':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")

        decoded = True

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_28[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('warning', "This sensor is not completed.")

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x30 Remote control and IR
    # ---------------------------------------
    if packettype == '30':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # Command type
        if subtype == '04':
            if ByteToHex(message[7]) == '00':
                cmndtype = "PC"
            elif ByteToHex(message[7]) == '01':
                cmndtype = "AUX1"
            elif ByteToHex(message[7]) == '02':
                cmndtype = "AUX2"
            elif ByteToHex(message[7]) == '03':
                cmndtype = "AUX3"
            elif ByteToHex(message[7]) == '04':
                cmndtype = "AUX4"
            else:
                cmndtype = "Unknown"

        # Command
        if subtype == '00':
            command = rfx.rfx_subtype_30_atiremotewonder[ByteToHex(message[5])]
        elif subtype == '01':
            command = "Not implemented in RFXCMD"
        elif subtype == '02':
            command = rfx.rfx_subtype_30_medion[ByteToHex(message[5])]
        elif subtype == '03':
            command = "Not implemented in RFXCMD"
        elif subtype == '04':
            command = "Not implemented in RFXCMD"

        toggle = ByteToHex(message[6])

        if subtype == '00' or subtype == '02' or subtype == '03':
            signal = rfxdecode.decode_signal(message[6])

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_30[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + id1)
        log_me('info', "Command\t\t\t= " + command)
        if subtype == '04':
            log_me('info', "Toggle\t\t\t= " + toggle)
        if subtype == '04':
            log_me('info', "CommandType\t= " + cmndtype)
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        if subtype == '00' or subtype == '02':
            output_me(timestamp, message, packettype, subtype, seqnbr, [
                ('signal_level', signal),
                ('id', id1),
                ('command', command)])
        elif subtype == '04' or subtype == '01' or subtype == '03':
            output_me(timestamp, message, packettype, subtype, seqnbr, [])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", id1)
                    action = action.replace("$command$", command)
                    if subtype == '04':
                        action = action.replace("$toggle$", toggle)
                        action = action.replace("$command$", cmndtype)
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x40 - Thermostat1
    # Credit: Jean-François Pucheu
    # ---------------------------------------
    if packettype == '40':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        temperature = int(ByteToHex(message[6]), 16)
        temperature_set = int(ByteToHex(message[7]), 16)
        status_temp = str(testBit(int(ByteToHex(message[8]), 16), 0) + \
                          testBit(int(ByteToHex(message[8]), 16), 1))
        status = rfx.rfx_subtype_40_status[status_temp]
        if testBit(int(ByteToHex(message[8]), 16), 7) == 128:
            mode = rfx.rfx_subtype_40_mode['1']
        else:
            mode = rfx.rfx_subtype_40_mode['0']
        signal = rfxdecode.decode_signal(message[9])

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_40[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + sensor_id)
        log_me('info', "Temperature\t\t= " + str(temperature) + " C")
        log_me('info', "Temperature set\t\t= " + str(temperature_set) + " C")
        log_me('info', "Mode\t\t\t= " + mode)
        log_me('info', "Status\t\t\t= " + status)
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [
            ('signal_level', signal),
            ('mode', mode),
            ('status', status),
            ('temperature_set', temperature_set),
            ('temperature', temperature)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$temperature$", str(temperature))
                    action = action.replace("$temperatureset$", str(temperature_set))
                    action = action.replace("$mode$", mode)
                    action = action.replace("$status$", status)
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x41 Thermostat2
    # ---------------------------------------
    if packettype == '41':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_41[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x42 Thermostat3
    # ---------------------------------------
    if packettype == '42':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        if subtype == '00':
            unitcode = ByteToHex(message[4])
        elif subtype == '01':
            unitcode = ByteToHex(message[4]) + ByteToHex(message[5]) + ByteToHex(message[6])
        else:
            unitcode = "00"

        log_me('debug', "Unitcode: " + unitcode)

        if subtype == '00':
            command = rfx.rfx_subtype_42_cmd00[ByteToHex(message[7])]
        elif subtype == '01':
            command = rfx.rfx_subtype_42_cmd01[ByteToHex(message[7])]
        else:
            command = '0'

        log_me('debug', "Command: " + command)

        signal = rfxdecode.decode_signal(message[8])

        # PRINTOUT
        log_me('debug', "Printout data")
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_42[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Unitcode\t\t= " + unitcode)
        log_me('info', "Command\t\t\t= " + command)
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [
            ('signal_level', signal),
            ('unitcode', unitcode),
            ('command', command)])

        # TRIGGER
        if config.trigger_active:
            log_me('debug', "Check trigger")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$unitcode$", unitcode)
                    action = action.replace("$command$", command)
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x50 - Temperature sensors
    # ---------------------------------------
    if packettype == '50':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        temperature = rfxdecode.decode_temperature(message[6], message[7])
        signal = rfxdecode.decode_signal(message[8])
        battery = rfxdecode.decode_battery(message[8])

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_50[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + sensor_id)
        log_me('info', "Temperature\t\t= " + temperature + " C")
        log_me('info', "Battery\t\t\t= " + str(battery))
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [
            ('id', sensor_id),
            ('battery', battery),
            ('signal_level', signal),
            ('temperature', temperature)])

        # TRIGGER
        if config.trigger_active:
            log_me('debug', "Check trigger")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$temperature$", str(temperature))
                    action = action.replace("$battery$", str(battery))
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return
                else:
                    log_me('debug', "No trigger match")

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x51 - Humidity sensors
    # ---------------------------------------
    if packettype == '51':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        humidity = int(ByteToHex(message[6]), 16)
        humidity_status = rfx.rfx_subtype_51_humstatus[ByteToHex(message[7])]
        signal = rfxdecode.decode_signal(message[8])
        battery = rfxdecode.decode_battery(message[8])

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_51[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + sensor_id)
        log_me('info', "Humidity\t\t= " + str(humidity))
        log_me('info', "Humidity Status\t\t= " + humidity_status)
        log_me('info', "Battery\t\t\t= " + str(battery))
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [
            ('id', sensor_id),
            ('humidity_status', humidity_status),
            ('humidity', humidity),
            ('battery', battery),
            ('signal_level', signal)])

        # TRIGGER
        if config.trigger_active:
            log_me('debug', "Check trigger")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$humidity$", str(humidity))
                    action = action.replace("$battery$", str(battery))
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x52 - Temperature and humidity sensors
    # ---------------------------------------
    if packettype == '52':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        temperature = rfxdecode.decode_temperature(message[6], message[7])
        humidity = int(ByteToHex(message[8]), 16)
        humidity_status = rfx.rfx_subtype_52_humstatus[ByteToHex(message[9])]
        signal = rfxdecode.decode_signal(message[10])
        battery = rfxdecode.decode_battery(message[10])

        # PRINTOUT
        log_me('debug', "Print data stdout")
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_52[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + sensor_id)
        log_me('info', "Temperature\t\t= " + temperature + " C")
        log_me('info', "Humidity\t\t= " + str(humidity) + "%")
        log_me('info', "Humidity Status\t\t= " + humidity_status)
        log_me('info', "Battery\t\t\t= " + str(battery))
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [
            ('id', sensor_id),
            ('humidity_status', humidity_status),
            ('temperature', temperature),
            ('humidity', humidity),
            ('battery', battery),
            ('signal_level', signal)])

        # TRIGGER
        if config.trigger_active:
            log_me('debug', "Check trigger")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$temperature$", str(temperature))
                    action = action.replace("$humidity$", str(humidity))
                    action = action.replace("$battery$", str(battery))
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x53 - Barometric
    # RESERVED FOR FUTURE
    # ---------------------------------------

    # ---------------------------------------
    # 0x54 - Temperature, humidity and barometric sensors
    # Credit: Jean-Baptiste Bodart
    # ---------------------------------------
    if packettype == '54':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        temperature = rfxdecode.decode_temperature(message[6], message[7])
        humidity = int(ByteToHex(message[8]), 16)
        try:
            humidity_status = rfx.rfx_subtype_54_humstatus[ByteToHex(message[9])]
        except Exception, err:
            log_me('error', err)
            log_me('warning', "Humidity status [" + ByteToHex(message[9]) + \
                   "] is unknown (" + ByteToHex(message) + ")")
            humidity_status = "Unknown"
        barometric_high = ByteToHex(message[10])
        barometric_low = ByteToHex(message[11])
        barometric_high = clearBit(int(barometric_high, 16), 7)
        barometric_high = barometric_high << 8
        barometric = (barometric_high + int(barometric_low, 16))
        if config.barometric != 0:
            barometric = int(barometric) + int(config.barometric)
        forecast = rfx.rfx_subtype_54_forecast[ByteToHex(message[12])]
        signal = rfxdecode.decode_signal(message[13])
        battery = rfxdecode.decode_battery(message[13])

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= %s " % str(rfx.rfx_subtype_54[subtype]))
        log_me('info', "Seqnbr\t\t\t= %s " % str(seqnbr))
        log_me('info', "Id\t\t\t= %s " % str(sensor_id))
        log_me('info', "Temperature\t\t= %s C " % str(temperature))
        log_me('info', "Humidity\t\t= %s " % str(humidity))
        if humidity_status:
            log_me('info', "Humidity Status\t\t= %s " % str(humidity_status))
        log_me('info', "Barometric pressure\t= %s hPa" % str(barometric))
        log_me('info', "Forecast Status\t\t= %s " % str(forecast))
        log_me('info', "Signal level\t\t= %s " % str(signal))
        log_me('info', "Battery\t\t\t= %s " % str(battery))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [
            ('battery', battery),
            ('signal_level', signal),
            ('id', sensor_id),
            ('forecast_status', forecast),
            ('humidity_status', humidity_status),
            ('humidity', humidity),
            ('barometric_pressure', barometric),
            ('temperature', temperature)])

        # TRIGGER
        if config.trigger_active:
            log_me('debug', "Trigger")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$temperature$", str(temperature))
                    action = action.replace("$humidity$", str(humidity))
                    action = action.replace("$barometric$", str(barometric))
                    action = action.replace("$battery$", str(battery))
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x55 - Rain sensors
    # ---------------------------------------
    if packettype == '55':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        rainrate_high = ByteToHex(message[6])
        rainrate_low = ByteToHex(message[7])
        if subtype == '01':
            rainrate = int(rainrate_high, 16) * 0x100 + int(rainrate_low, 16)
        elif subtype == '02':
            rainrate = float(int(rainrate_high, 16) * 0x100 + int(rainrate_low, 16)) / 100
        else:
            rainrate = 0
        raintotal1 = ByteToHex(message[8])
        raintotal2 = ByteToHex(message[9])
        raintotal3 = ByteToHex(message[10])
        if subtype != '06':
            raintotal = float((int(raintotal1, 16) * 0x1000) + \
                        (int(raintotal2, 16) * 0x100) + int(raintotal3, 16)) / 10
        else:
            raintotal = 0
        signal = rfxdecode.decode_signal(message[11])
        battery = rfxdecode.decode_battery(message[11])

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_55[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + sensor_id)

        if subtype == '01' or subtype == '02':
            log_me('info', "Rain rate\t\t= " + str(rainrate) + " mm/hr")

        if subtype != '06':
            log_me('info', "Raintotal:\t\t= " + str(raintotal) + " mm")
        else:
            log_me('info', "Raintotal:\t\t= Not implemented in rfxcmd, need example data")

        log_me('info', "Battery\t\t\t= " + str(battery))
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [
            ('rainrate', rainrate),
            ('battery', battery),
            ('id', sensor_id),
            ('signal_level', signal)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$rainrate$", str(rainrate))
                    action = action.replace("$raintotal$", str(raintotal))
                    action = action.replace("$battery$", str(battery))
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x56 - Wind sensors
    # ---------------------------------------
    if packettype == '56':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        direction = ((int(ByteToHex(message[6]), 16) * 256) + \
                    int(ByteToHex(message[7]), 16))
        if subtype != "05":
            av_speed = ((int(ByteToHex(message[8]), 16) * 256) + \
                       int(ByteToHex(message[9]), 16)) * 0.1
        else:
            av_speed = 0
        gust = ((int(ByteToHex(message[10]), 16) * 256) + \
               int(ByteToHex(message[11]), 16)) * 0.1
        if subtype == "04":
            temperature = rfxdecode.decode_temperature(message[12], message[13])
        else:
            temperature = 0
        if subtype == "04":
            windchill = rfxdecode.decode_temperature(message[14], message[15])
        else:
            windchill = 0
        signal = rfxdecode.decode_signal(message[16])
        battery = rfxdecode.decode_battery(message[16])
        display_subtype = rfx.rfx_subtype_56[subtype]

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + display_subtype)
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + sensor_id)
        log_me('info', "Wind direction\t\t= " + str(direction) + " degrees")
        if subtype != "05":
            log_me('info', "Average wind\t\t= " + str(av_speed) + " mtr/sec")
        if subtype == "04":
            log_me('info', "Temperature\t\t= " + str(temperature) + " C")
            log_me('info', "Wind chill\t\t= " + str(windchill) + " C")
        log_me('info', "Windgust\t\t= " + str(gust) + " mtr/sec")
        log_me('info', "Battery\t\t\t= " + str(battery))
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, display_subtype, seqnbr, [
            ('battery', battery),
            ('signal_level', signal),
            ('id', sensor_id),
            ('temperature', temperature),
            ('wind_average_speed', av_speed),
            ('wind_gust', gust),
            ('wind_direction', direction),
            ('wind_chill', windchill)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$direction$", str(direction))
                    if subtype != "05":
                        action = action.replace("$average$", str(av_speed))
                    if subtype == "04":
                        action = action.replace("$temperature$", str(temperature))
                        action = action.replace("$windchill$", str(windchill))
                    action = action.replace("$windgust$", str(gust))
                    action = action.replace("$battery$", str(battery))
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x57 UV Sensor
    # ---------------------------------------
    if packettype == '57':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        ultra_violet = int(ByteToHex(message[6]), 16) * 10
        temperature = rfxdecode.decode_temperature(message[6], message[8])
        signal = rfxdecode.decode_signal(message[9])
        battery = rfxdecode.decode_battery(message[9])

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_57[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + sensor_id)
        log_me('info', "UV\t\t\t= " + str(ultra_violet))
        if subtype == '03':
            log_me('info', "Temperature\t\t= " + temperature + " C")
        log_me('info', "Battery\t\t\t= " + str(battery))
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        if subtype == '03':
            output_me(timestamp, message, packettype, subtype, seqnbr, [
                ('id', sensor_id),
                ('ultra_violet', ultra_violet),
                ('temperature', temperature),
                ('battery', battery),
                ('signal_level', signal)])
        else:
            output_me(timestamp, message, packettype, subtype, seqnbr, [
                ('id', sensor_id),
                ('ultra_violet', ultra_violet),
                ('battery', battery),
                ('signal_level', signal)])

        # TRIGGER
        if config.trigger_active:
            log_me('debug', "Trigger action")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$uv$", str(ultra_violet))
                    if subtype == '03':
                        action = action.replace("$temperature$", str(temperature))
                    action = action.replace("$battery$", str(battery))
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x58 Date/Time sensor
    # ---------------------------------------
    if packettype == '58':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        date_yy = int(ByteToHex(message[6]), 16)
        date_mm = int(ByteToHex(message[7]), 16)
        date_dd = int(ByteToHex(message[8]), 16)
        date_string = "20%s-%s-%s" % (
            str(date_yy).zfill(2),
            str(date_mm).zfill(2),
            str(date_dd).zfill(2))
        date_dow = int(ByteToHex(message[9]), 16)
        time_hr = int(ByteToHex(message[10]), 16)
        time_min = int(ByteToHex(message[11]), 16)
        time_sec = int(ByteToHex(message[12]), 16)
        time_string = "%s:%s:%s" % (str(time_hr), str(time_min), str(time_sec))
        datetime_string = "%s %s" % (str(date_string), str(time_string))
        log_me('debug', "DateTime: %s" % str(datetime_string))
        signal = rfxdecode.decode_signal(message[13])
        battery = rfxdecode.decode_battery(message[13])

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= %s" % str(rfx.rfx_subtype_58[subtype]))
        log_me('info', "Seqnbr\t\t\t= %s" % str(seqnbr))
        log_me('info', "Id\t\t\t= %s" % str(sensor_id))
        log_me('info', "Time\t\t\t= %s" % str(time_string))
        log_me('info', "Date (yy-mm-dd)\t\t= %s" % str(date_string))
        log_me('info', "Day of week (1-7)\t= %s" % str(date_dow))
        log_me('info', "Battery\t\t\t= %s" % str(battery))
        log_me('info', "Signal level\t\t= %s" % str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [
            ('id', sensor_id),
            ('time', time_string),
            ('date', date_string),
            ('day_of_week', date_dow),
            ('battery', battery),
            ('signal_level', signal)])

        # TRIGGER
        if config.trigger_active:
            log_me('debug', "Trigger action")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$date$", str(date_string))
                    action = action.replace("$time$", str(time_string))
                    action = action.replace("$dow$", str(date_dow))
                    action = action.replace("$battery$", str(battery))
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x59 Current Sensor
    # ---------------------------------------
    if packettype == '59':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        count = int(ByteToHex(message[6]), 16)
        channel1 = (int(ByteToHex(message[7]), 16) * 0x100 + int(ByteToHex(message[8]), 16)) * 0.1
        channel2 = (int(ByteToHex(message[9]), 16) * 0x100 + int(ByteToHex(message[10]), 16)) * 0.1
        channel3 = (int(ByteToHex(message[11]), 16) * 0x100 + int(ByteToHex(message[12]), 16)) * 0.1
        signal = rfxdecode.decode_signal(message[13])
        battery = rfxdecode.decode_battery(message[13])

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_5A[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + sensor_id)
        log_me('info', "Counter\t\t\t= " + str(count))
        log_me('info', "Channel 1\t\t= " + str(channel1) + "A")
        log_me('info', "Channel 2\t\t= " + str(channel2) + "A")
        log_me('info', "Channel 3\t\t= " + str(channel3) + "A")
        log_me('info', "Battery\t\t\t= " + str(battery))
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$counter$", str(count))
                    action = action.replace("$channel1$", str(channel1))
                    action = action.replace("$channel2$", str(channel2))
                    action = action.replace("$channel3$", str(channel3))
                    action = action.replace("$battery$", str(battery))
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x5A Energy sensor
    # Credit: Jean-Michel ROY
    # ---------------------------------------
    if packettype == '5A':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        signal = rfxdecode.decode_signal(message[17])
        count = int(ByteToHex(message[6]), 16)
        battery = rfxdecode.decode_battery(message[17])
        instant = int(ByteToHex(message[7]), 16) * 0x1000000 + \
                  int(ByteToHex(message[8]), 16) * 0x10000 + \
                  int(ByteToHex(message[9]), 16) * 0x100  + \
                  int(ByteToHex(message[10]), 16)
        usage = int((
            int(ByteToHex(message[11]), 16) * 0x10000000000 + \
            int(ByteToHex(message[12]), 16) * 0x100000000 + \
            int(ByteToHex(message[13]), 16) * 0x1000000 + \
            int(ByteToHex(message[14]), 16) * 0x10000 + \
            int(ByteToHex(message[15]), 16) * 0x100 + \
            int(ByteToHex(message[16]), 16)) / 223.666)

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_5A[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + sensor_id)
        log_me('info', "Count\t\t\t= " + str(count))
        log_me('info', "Instant usage\t\t= " + str(instant) + " Watt")
        log_me('info', "Total usage\t\t= " + str(usage) + " Wh")
        log_me('info', "Battery\t\t\t= " + str(battery))
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [
            ('id', sensor_id),
            ('instant_usage', instant),
            ('total_usage', usage),
            ('battery', battery),
            ('signal_level', signal)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$count$", str(count))
                    action = action.replace("$instant$", str(instant))
                    action = action.replace("$total$", str(usage))
                    action = action.replace("$battery$", str(battery))
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x5B Current Sensor
    # ---------------------------------------
    if packettype == '5B':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        count = int(ByteToHex(message[6]), 16)
        channel1 = (int(ByteToHex(message[7]), 16) * 0x100 + int(ByteToHex(message[8]), 16)) * 0.1
        channel2 = (int(ByteToHex(message[9]), 16) * 0x100 + int(ByteToHex(message[10]), 16)) * 0.1
        channel3 = (int(ByteToHex(message[11]), 16) * 0x100 + int(ByteToHex(message[12]), 16)) * 0.1
        total = float((
            int(ByteToHex(message[13]), 16) * 0x10000000000 + \
            int(ByteToHex(message[14]), 16) * 0x100000000 + \
            int(ByteToHex(message[15]), 16) * 0x1000000 + \
            int(ByteToHex(message[16]), 16) * 0x10000 + \
            int(ByteToHex(message[17]), 16) * 0x100 + \
            int(ByteToHex(message[18]), 16)) / 223.666)
        signal = rfxdecode.decode_signal(message[19])
        battery = rfxdecode.decode_battery(message[19])

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_5B[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + sensor_id)
        log_me('info', "Counter\t\t\t= " + str(count))
        log_me('info', "Channel 1\t\t= " + str(channel1) + "A")
        log_me('info', "Channel 2\t\t= " + str(channel2) + "A")
        log_me('info', "Channel 3\t\t= " + str(channel3) + "A")
        if total != 0:
            log_me('info', "Total\t\t\t= %s Wh" % str(round(total, 1)))
        log_me('info', "Battery\t\t\t= " + str(battery))
        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$counter$", str(count))
                    action = action.replace("$channel1$", str(channel1))
                    action = action.replace("$channel2$", str(channel2))
                    action = action.replace("$channel3$", str(channel3))
                    action = action.replace("$battery$", str(battery))
                    action = action.replace("$signal$", str(signal))
                    action = action.replace("$total$", str(total))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x5C Power Sensors
    # ---------------------------------------
    if packettype == '5C':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2
        voltage = int(ByteToHex(message[6]), 16)
        current = (int(ByteToHex(message[7]), 16) * 0x100 + int(ByteToHex(message[8]), 16)) * 0.01
        power = (int(ByteToHex(message[9]), 16) * 0x100 + int(ByteToHex(message[10]), 16)) * 0.1
        energy = (int(ByteToHex(message[11]), 16) * 0x100 + int(ByteToHex(message[12]), 16)) * 0.01
        powerfactor = (int(ByteToHex(message[13]), 16)) * 0.01
        freq = int(ByteToHex(message[14]), 16)
        signal = rfxdecode.decode_signal(message[15])

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= %s" % str(rfx.rfx_subtype_5C[subtype]))
        log_me('info', "Seqnbr\t\t\t= %s" % str(seqnbr))
        log_me('info', "Id\t\t\t= %s" % str(sensor_id))
        log_me('info', "Voltage\t\t\t= %s Volt" % (str(voltage)))
        log_me('info', "Current\t\t\t= %s Ampere" % str(current))
        log_me('info', "Instant power\t\t= %s Watt" % str(power))
        log_me('info', "Total usage\t\t= %s kWh" % str(energy))
        log_me('info', "Power factor\t\t= %s " % str(powerfactor))
        log_me('info', "Frequency\t\t= %s Hz" % str(freq))
        log_me('info', "Signal level\t\t= %s" % str(signal))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", str(sensor_id))
                    action = action.replace("$voltage$", str(voltage))
                    action = action.replace("$current$", str(current))
                    action = action.replace("$powerfactor$", str(powerfactor))
                    action = action.replace("$frequency$", str(freq))
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x5E Gas Usage Sensor
    # ---------------------------------------
    if packettype == '5E':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")

        decoded = True

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_5E[subtype])
        log_me('warning', "This sensor is not completed.")

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x5F Water Usage Sensor
    # ---------------------------------------
    if packettype == '5F':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")

        decoded = True

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_5F[subtype])
        log_me('warning', "This sensor is not completed.")

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x70 RFXsensor
    # ---------------------------------------
    if packettype == '70':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        if subtype == '00':
            temperature = float(rfxdecode.decode_temperature(message[5], message[6]))
            temperature = temperature * 0.1
        else:
            temperature = 0
        if subtype == '01' or subtype == '02':
            voltage_hi = int(ByteToHex(message[5]), 16) * 256
            voltage_lo = int(ByteToHex(message[6]), 16)
            voltage = voltage_hi + voltage_lo
        else:
            voltage = 0
        signal = rfxdecode.decode_signal(message[7])

        if subtype == '03':
            sensor_message = rfx.rfx_subtype_70_msg03[message[6]]

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_70[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + id1)

        if subtype == '00':
            log_me('info', "Temperature\t\t= " + str(temperature) + " C")

        if subtype == '01' or subtype == '02':
            log_me('info', "Voltage\t\t\t= " + str(voltage) + " mV")

        if subtype == '03':
            log_me('info', "Message\t\t\t= " + sensor_message)

        log_me('info', "Signal level\t\t= " + str(signal))

        # OUTPUT
        if subtype == '00':
            output_me(timestamp, message, packettype, subtype, seqnbr, [
                ('signal_level', signal),
                ('id', id1),
                ('temperature', temperature)])
        if subtype == '01' or subtype == '02':
            output_me(timestamp, message, packettype, subtype, seqnbr, [
                ('signal_level', signal),
                ('id', id1),
                ('voltage', voltage)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", id1)
                    if subtype == '00':
                        action = action.replace("$temperature$", str(temperature))
                    if subtype == '01' or subtype == '02':
                        action = action.replace("$voltage$", str(voltage))
                    if subtype == '03':
                        action = action.replace("$message$", sensor_message)
                    action = action.replace("$signal$", str(signal))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x71 RFXmeter
    # ---------------------------------------
    if packettype == '71':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")

        decoded = True

        # DATA
        sensor_id = id1 + id2
        sensor_power = ''

        try:
            sensor_power = rfxdecode.decode_power(message[7], message[8], message[9])
        except Exception, err:
            log_me('error', err)

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_71[subtype])
        log_me('info', "Seqnbr\t\t\t= " + seqnbr)
        log_me('info', "Id\t\t\t= " + id1)
        log_me('info', "Power\t\t\t= " + str(sensor_power))

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [
            ('id', sensor_id),
            ('power', sensor_power)])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    action = action.replace("$id$", id1)
                    action = action.replace("$power$", str(sensor_power))
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x72 FS20
    # ---------------------------------------
    if packettype == '72':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")

        decoded = True

        # PRINTOUT
        log_me('info', "Subtype\t\t\t= " + rfx.rfx_subtype_72[subtype])
        log_me('warning', "This sensor is not completed.")

        # OUTPUT
        output_me(timestamp, message, packettype, subtype, seqnbr, [])

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex(message)
                rawcmd = rawcmd.replace(' ', '')
                if match(trigger_message, rawcmd):
                    log_me('debug', "Trigger match")
                    log_me('debug', "Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message)
                    action = action.replace("$packettype$", packettype)
                    action = action.replace("$subtype$", subtype)
                    log_me('debug', "Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        log_me('debug', "Trigger onematch active, exit trigger")
                        return

        log_me('debug', "Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # Not decoded message
    # ---------------------------------------

    # The packet is not decoded, then log_me('info', it on the screen)
    if not decoded:
        log_me('error', "Message not decoded. Line: " + _line())
        log_me('error', "Message: " + ByteToHex(message))
        log_me('info', timestamp + " " + ByteToHex(message))
        log_me('info', "RFXCMD cannot decode message, see http://code.google.com/p/rfxcmd/wiki/")

    # decodePackage END
    return

# ----------------------------------------------------------------------------

def read_socket():
    """
    Check socket for messages

    Credit: Olivier Djian
    """

    if not MESSAGEQUEUE.empty():
        log_me('debug', "Message received in socket MESSAGEQUEUE")
        message = stripped(MESSAGEQUEUE.get())

        if test_rfx(message):

            if config.serial_active:
                # Flush buffer
                serial_param.port.flushOutput()
                log_me('debug', "SerialPort flush output")
                serial_param.port.flushInput()
                log_me('debug', "SerialPort flush input")

            timestamp = strftime('%Y-%m-%d %H:%M:%S')

            log_me('info', "------------------------------------------------")
            log_me('info', "Incoming message from socket")
            log_me('info', "Send\t\t\t= " + ByteToHex(message.decode('hex')))
            log_me('info', "Date/Time\t\t\t= " + timestamp)
            log_me('info', "Packet Length\t\t= " + ByteToHex(message.decode('hex')[0]))

            try:
                log_me('debug', "Decode message")
                decode_packet(message.decode('hex'))
            except KeyError:
                log_me('error', "Unrecognizable packet. Line: " + _line())

            if config.serial_active:
                log_me('debug', "Write message to serial port")
                serial_param.port.write(message.decode('hex'))

        else:
            log_me('error', "Invalid message from socket. Line: " + _line())

# ----------------------------------------------------------------------------

def test_rfx(message):
    """
    Test, filter and verify that the incoming message is valid
    Return true if valid, False if not
    """

    log_me('debug', "Test message: " + message)

    # Remove all invalid characters
    message = stripped(message)

    # Remove any whitespaces
    try:
        message = message.replace(' ', '')
    except Exception:
        log_me('error', "Removing white spaces")
        return False

    # Test the string if it is hex format
    try:
        int(message, 16)
    except Exception:
        log_me('error', "Packet not hex format")
        return False

    # Check that length is even
    if len(message) % 2:
        log_me('error', "Packet length not even")
        return False

    # Check that first byte is not 00
    if ByteToHex(message.decode('hex')[0]) == "00":
        log_me('error', "Packet first byte is 00")
        return False

    # Length more than one byte
    if not len(message.decode('hex')) > 1:
        log_me('error', "Packet is not longer than one byte")
        return False

    # Check if string is the length that it reports to be
    cmd_len = int(ByteToHex(message.decode('hex')[0]), 16)
    if not len(message.decode('hex')) == (cmd_len + 1):
        log_me('error', "Packet length is not valid")
        return False

    log_me('debug', "Message OK")

    return True

# ----------------------------------------------------------------------------

def send_rfx(message):
    """
    Decode and send raw message to RFX device
    """
    timestamp = strftime("%Y-%m-%d %H:%M:%S")

    log_me('info', "------------------------------------------------")
    log_me('info', "Send\t\t\t= " + ByteToHex(message))
    log_me('info', "Date/Time\t\t\t= " + timestamp)
    log_me('info', "Packet Length\t\t= " + ByteToHex(message[0]))

    try:
        decode_packet(message)
    except KeyError, err:
        log_me('error', "unrecognizable packet %s" % err)

    serial_param.port.write(message)
    sleep(1)

# ----------------------------------------------------------------------------

def read_rfx():
    """
    Read message from RFXtrx and decode the decode the message
    """
    message = None
    byte = None

    try:

        try:
            if serial_param.port.inWaiting() != 0:
                timestamp = strftime("%Y-%m-%d %H:%M:%S")
                log_me('debug', "Timestamp: " + timestamp)
                log_me('debug', "SerWaiting: " + str(serial_param.port.inWaiting()))
                byte = serial_param.port.read()
                log_me('debug', "Byte: " + str(ByteToHex(byte)))
        except IOError, err:
            log_me('error', err)
            log_me('error', "Serial read %s, Line: %s" % (str(err), _line()))

        if byte:
            message = byte + readbytes(ord(byte))
            log_me('debug', "Message: " + str(ByteToHex(message)))

            # First byte indicate length of message, must be other than 00
            if ByteToHex(message[0]) != "00":

                # Verify length
                log_me('debug', "Verify length")
                if (len(message) - 1) == ord(message[0]):

                    log_me('debug', "Length OK")

                    # Whitelist
                    if config.whitelist_active:
                        log_me('debug', "Check whitelist")
                        whitelist_match = False
                        for sensor in whitelist.data:
                            sensor = sensor.childNodes[0].nodeValue
                            log_me('debug', "Tag: " + sensor)
                            rawcmd = ByteToHex(message)
                            rawcmd = rawcmd.replace(' ', '')
                            if match(sensor, rawcmd):
                                log_me('debug', "Whitelist match")
                                whitelist_match = True

                        if not whitelist_match:
                            log_me('info', "Sensor not included in whitelist")
                            return rawcmd

                    log_me('info', "------------------------------------------------")
                    log_me('info', "Received\t\t\t= " + ByteToHex(message))
                    log_me('info', "Date/Time\t\t\t= " + timestamp)
                    log_me('info', "Packet Length\t\t= " + ByteToHex(message[0]))

                    log_me('debug', 'Decode packet')
                    try:
                        decode_packet(message)
                    except KeyError, err:
                        log_me('error', "unrecognizable packet (" + ByteToHex(message) + \
                               ") Line: " + _line())
                        log_me('error', err)
                    rawcmd = ByteToHex(message)
                    rawcmd = rawcmd.replace(' ', '')

                    return rawcmd

                else:
                    log_me('error', "Incoming packet not valid length. Line: "  + _line())
                    log_me('error', "------------------------------------------------")
                    log_me('error', "Received\t\t\t= " + ByteToHex(message))
                    log_me('error', "Incoming packet not valid, waiting for next...")

    except OSError:
        log_me('error', "Error in message: " + str(ByteToHex(message)) + " Line: " + _line())
        log_me('error', "Traceback: " + format_exc())
        log_me('error', "------------------------------------------------")
        log_me('error', "Received\t\t\t= " + ByteToHex(message))
        format_exc()

# ----------------------------------------------------------------------------

def read_config(configFile, configItem):
    """
    Read item from the configuration file
    """
    log_me('debug', 'Open configuration file')
    log_me('debug', 'File: ' + configFile)

    if os.path.exists(configFile):

        #open the xml file for reading:
        config_file = open(configFile, 'r')
        data = config_file.read()
        config_file.close()

        # xml parse file data
        log_me('debug', 'Parse config XML data')
        try:
            dom = minidom.parseString(data)
        except Exception, err:
            log_me('error', "problem in the config.xml file, cannot process it")
            log_me('error', err)

        # Get config item
        log_me('debug', 'Get the configuration item: ' + configItem)

        try:
            xml_tag = dom.getElementsByTagName(configItem)[0].toxml()
            log_me('debug', 'Found: ' + xml_tag)
            xml_data = xml_tag.replace('<' + configItem + '>', '').\
                replace('</' + configItem + '>', '')
            log_me('debug', '--> ' + xml_data)
        except Exception, err:
            log_me('error', 'The item tag not found in the config file')
            log_me('error', err)
            xml_data = ""

        log_me('debug', 'Return')

    else:
        log_me('error', "Config file does not exists. Line: " + _line())

    return xml_data

# ----------------------------------------------------------------------------

def read_whitelistfile():
    """
    Read whitelist file to list
    """
    try:
        xmldoc = minidom.parse(config.whitelist_file)
    except Exception, err:
        log_me('error', "Error in " + config.whitelist_file + " file")
        log_me('error', err)
        exit(1)

    whitelist.data = xmldoc.documentElement.getElementsByTagName('sensor')

    for sensor in whitelist.data:
        log_me('debug', "Tags: " + sensor.childNodes[0].nodeValue)

# ----------------------------------------------------------------------------

def read_triggerfile():
    """
    Read trigger file to list
    """
    try:
        xmldoc = minidom.parse(config.trigger_file)
    except Exception, err:
        log_me('error', "Error in " + config.trigger_file + " file")
        log_me('error', err)
        exit(1)

    triggerlist.data = xmldoc.documentElement.getElementsByTagName('trigger')

    for trigger in triggerlist.data:
        message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
        action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
        log_me('debug', "Message: " + message + ", Action: " + action)

# ----------------------------------------------------------------------------

def print_version():
    """
    Print RFXCMD version, build and date
    """
    log_me('debug', "print_version")
    log_me('info', "RFXCMD Version: " + __version__)
    log_me('info', __date__.replace('$', ''))
    log_me('debug', "Exit 0")
    exit(0)

# ----------------------------------------------------------------------------

def check_pythonversion():
    """
    Check python version
    """
    if sys.hexversion < 0x02060000:
        log_me('error', "Your Python need to be 2.6 or newer, please upgrade.")
        exit(1)

# ----------------------------------------------------------------------------

def option_simulate(indata):
    """
    Simulate incoming packet, decode and process
    """

    # Remove all spaces
    for i in whitespace:
        indata = indata.replace(i, "")

    # Cut into hex chunks
    try:
        message = indata.decode("hex")
    except Exception, err:
        log_me('error', "the input data is not valid. Line: " + _line())
        log_me('error', err)
        exit(1)

    timestamp = strftime('%Y-%m-%d %H:%M:%S')

    # Whitelist
    if config.whitelist_active:
        log_me('debug', "Check whitelist")
        whitelist_match = False
        for sensor in whitelist.data:
            sensor = sensor.getElementsByTagName('sensor')[0].childNodes[0].nodeValue
            log_me('debug', "Sensor: " + sensor)
            rawcmd = ByteToHex(message)
            rawcmd = rawcmd.replace(' ', '')
            if match(sensor, rawcmd):
                whitelist_match = True

        if not whitelist_match:
            log_me('info', "Sensor not included in whitelist")
            log_me('debug', "No match in whitelist")
            log_me('debug', "Exit 0")
            exit(0)

    # Printout
    log_me('info', "------------------------------------------------")
    log_me('info', "Received\t\t\t= " + indata)
    log_me('info', "Date/Time\t\t\t= " + timestamp)

    # Verify that the incoming value is hex
    try:
        int(indata, 16)
    except Exception, err:
        log_me('error', "the input data is invalid hex value. Line: " + _line())
        log_me('error', err)
        exit(1)

    # Decode it
    try:
        decode_packet(message)
    except Exception as err:
        log_me('error', "unrecognizable packet (" + ByteToHex(message) + ") Line: " + _line())
        log_me('error', err)

    log_me('debug', 'Exit 0')
    exit(0)

# ----------------------------------------------------------------------------

def option_listen():
    """
    Listen to RFXtrx device and process data, exit with CTRL+C
    """
    log_me('debug', "Start listening...")

    if config.serial_active:
        log_me('debug', "Open serial port")
        open_serialport()

    if config.socketserver:
        try:
            serversocket = RFXcmdSocketAdapter(config.sockethost, int(config.socketport))
        except Exception, err:
            log_me('error', "Error starting socket server. Line: " + _line())
            log_me('error', "can not start server socket, another instance already running?")
            log_me('error', err)
            exit(1)
        if serversocket.net_adapter_registered:
            log_me('debug', "Socket interface started")
        else:
            log_me('warning', "Cannot start socket interface")

    if config.serial_active:
        # Flush buffer
        log_me('debug', "Serialport flush output")
        serial_param.port.flushOutput()
        log_me('debug', "Serialport flush input")
        serial_param.port.flushInput()

        # Send RESET
        log_me('debug', "Send rfxcmd_reset (" + rfxcmd.reset + ")")
        serial_param.port.write(rfxcmd.reset.decode('hex'))
        log_me('debug', "Sleep 1 sec")
        sleep(1)

        # Flush buffer
        log_me('debug', "Serialport flush output")
        serial_param.port.flushOutput()
        log_me('debug', "Serialport flush input")
        serial_param.port.flushInput()

        # Send STATUS
        log_me('debug', "Send rfxcmd_status (" + rfxcmd.status + ")")
        serial_param.port.write(rfxcmd.status.decode('hex'))
        log_me('debug', "Sleep 1 sec")
        sleep(1)

        # If active (autostart)
        if config.protocol_startup:
            log_me('debug', "Protocol AutoStart activated")
            try:
                p_message = protocol.set_protocolfile(config.protocol_file)
                log_me('debug', "Send set protocol message (" + p_message + ")")
                serial_param.port.write(p_message.decode('hex'))
                log_me('debug', "Sleep 1 sec")
                sleep(1)
            except Exception as err:
                log_me('error', "Could not create protocol message")

    try:
        while 1:
            # Let it breath
            # Without this sleep it will cause 100% CPU in windows
            sleep(0.01)

            if config.serial_active:
                # Read serial port
                if config.process_rfxmsg:
                    rawcmd = read_rfx()
                    if rawcmd:
                        log_me('debug', "Processed: " + str(rawcmd))

            # Read socket
            if config.socketserver:
                read_socket()

    except KeyboardInterrupt:
        log_me('debug', "Received keyboard interrupt")
        log_me('debug', "Close server socket")
        serversocket.net_adapter.shutdown()

        if config.serial_active:
            log_me('debug', "Close serial port")
            close_serialport()

        log_me('info', "\nExit...")

# ----------------------------------------------------------------------------

def option_getstatus():
    """
    Get status from RFXtrx device and log_me('info', on screen)
    """

    # Flush buffer
    serial_param.port.flushOutput()
    serial_param.port.flushInput()

    # Send RESET
    serial_param.port.write(rfxcmd.reset.decode('hex'))
    sleep(1)

    # Flush buffer
    serial_param.port.flushOutput()
    serial_param.port.flushInput()

    # Send STATUS
    send_rfx(rfxcmd.status.decode('hex'))
    sleep(1)
    read_rfx()

# ----------------------------------------------------------------------------

def option_send():
    """
    Send command to RFX device

    """

    log_me('debug', "Send message to RFX device")

    # Open serial port
    log_me('debug', "Open serial port")
    open_serialport()

    # Remove any whitespaces
    cmdarg.rawcmd = cmdarg.rawcmd.replace(' ', '')
    log_me('debug', "Message: " + cmdarg.rawcmd)

    # Test the string if it is hex format
    try:
        int(cmdarg.rawcmd, 16)
    except ValueError:
        log_me('error', "invalid rawcmd, not hex format")
        exit(1)

    # Check that first byte is not 00
    if ByteToHex(cmdarg.rawcmd.decode('hex')[0]) == "00":
        log_me('error', "invalid rawcmd, first byte is zero")
        exit(1)

    # Check if string is the length that it reports to be
    cmd_len = int(ByteToHex(cmdarg.rawcmd.decode('hex')[0]), 16)
    if not len(cmdarg.rawcmd.decode('hex')) == (cmd_len + 1):
        log_me('error', "invalid rawcmd, invalid length")
        exit(1)

    # Flush buffer
    log_me('debug', "Serialport flush output")
    serial_param.port.flushOutput()
    log_me('debug', "Serialport flush input")
    serial_param.port.flushInput()

    # Send RESET
    log_me('debug', "Send RFX reset")
    serial_param.port.write(rfxcmd.reset.decode('hex'))
    sleep(1)

    # Flush buffer
    log_me('debug', "Serialport flush output")
    serial_param.port.flushOutput()
    log_me('debug', "Serialport flush input")
    serial_param.port.flushInput()

    if cmdarg.rawcmd:
        timestamp = strftime('%Y-%m-%d %H:%M:%S')
        log_me('info', "------------------------------------------------")
        log_me('info', "Send\t\t\t= " + ByteToHex(cmdarg.rawcmd.decode('hex')))
        log_me('info', "Date/Time\t\t\t= " + timestamp)
        log_me('info', "Packet Length\t\t= " + ByteToHex(cmdarg.rawcmd.decode('hex')[0]))
        try:
            decode_packet(cmdarg.rawcmd.decode('hex'))
        except KeyError:
            log_me('error', "unrecognizable packet")

        log_me('debug', "Send message")
        serial_param.port.write(cmdarg.rawcmd.decode('hex'))
        sleep(1)
        log_me('debug', "Read response")
        read_rfx()

    log_me('debug', "Close serial port")
    close_serialport()

# ----------------------------------------------------------------------------

def option_bsend():
    """
    Send command when rfxcmd is running
    Input: none

    NOTE! Will be depricated in v0.3 and removed in v0.31

    """

    log_me('info', "BSEND action is DEPRICATED, will be removed really soon...")

    log_me('debug', 'Action: bsend')

    # Remove any whitespaces
    cmdarg.rawcmd = cmdarg.rawcmd.replace(' ', '')
    log_me('debug', 'rawcmd: ' + cmdarg.rawcmd)

    # Test the string if it is hex format
    try:
        int(cmdarg.rawcmd, 16)
    except ValueError:
        log_me('error', "invalid rawcmd, not hex format")
        exit(1)

    # Check that first byte is not 00
    if ByteToHex(cmdarg.rawcmd.decode('hex')[0]) == "00":
        log_me('error', "invalid rawcmd, first byte is zero")
        exit(1)

    # Check if string is the length that it reports to be
    cmd_len = int(ByteToHex(cmdarg.rawcmd.decode('hex')[0]), 16)
    if not len(cmdarg.rawcmd.decode('hex')) == (cmd_len + 1):
        log_me('error', "invalid rawcmd, invalid length")
        exit(1)

    if cmdarg.rawcmd:
        serial_param.port.write(cmdarg.rawcmd.decode('hex'))

# ----------------------------------------------------------------------------

def read_configfile():
    """
    Read items from the configuration file
    """
    if os.path.exists(cmdarg.configfile):

        # ----------------------
        # Serial device
        config.serial_active = bool(read_config(cmdarg.configfile, "serial_active") == "yes")
        config.serial_device = read_config(cmdarg.configfile, "serial_device")
        config.serial_rate = read_config(cmdarg.configfile, "serial_rate")
        config.serial_timeout = read_config(cmdarg.configfile, "serial_timeout")

        log_me('debug', "Serial device: " + str(config.serial_device))
        log_me('debug', "Serial rate: " + str(config.serial_rate))
        log_me('debug', "Serial timeout: " + str(config.serial_timeout))

        # ----------------------
        # Process
        config.process_rfxmsg = bool(read_config(cmdarg.configfile, "process_rfxmsg") == "yes")
        log_me('debug', "Process RFXmsg: " + str(config.process_rfxmsg))

        # ----------------------
        # TRIGGER
        config.trigger_active = bool(read_config(cmdarg.configfile, "trigger_active") == "yes")
        config.trigger_onematch = bool(read_config(cmdarg.configfile, "trigger_onematch") == "yes")
        config.trigger_file = read_config(cmdarg.configfile, "trigger_file")
        config.trigger_timeout = read_config(cmdarg.configfile, "trigger_timeout")

        # ----------------------
        # SOCKET SERVER
        config.socketserver = bool(read_config(cmdarg.configfile, "socketserver") == "yes")
        config.sockethost = read_config(cmdarg.configfile, "sockethost")
        config.socketport = read_config(cmdarg.configfile, "socketport")
        log_me('debug', "SocketServer: " + str(config.socketserver))
        log_me('debug', "SocketHost: " + str(config.sockethost))
        log_me('debug', "SocketPort: " + str(config.socketport))

        # -----------------------
        # WHITELIST
        config.whitelist_active = bool(read_config(cmdarg.configfile, "whitelist_active") == "yes")
        config.whitelist_file = read_config(cmdarg.configfile, "whitelist_file")
        log_me('debug', "Whitelist_active: " + str(config.whitelist_active))
        log_me('debug', "Whitelist_file: " + str(config.whitelist_file))

        # -----------------------
        # DAEMON
        config.daemon_active = bool(read_config(cmdarg.configfile, "daemon_active") == "yes")
        config.daemon_pidfile = read_config(cmdarg.configfile, "daemon_pidfile")
        log_me('debug', "Daemon_active: " + str(config.daemon_active))
        log_me('debug', "Daemon_pidfile: " + str(config.daemon_pidfile))

        # ------------------------
        # BAROMETRIC
        config.barometric = read_config(cmdarg.configfile, "barometric")

        # ------------------------
        # LOG MESSAGES
        config.log_msg = bool(read_config(cmdarg.configfile, "log_msg") == "yes")
        config.log_msgfile = read_config(cmdarg.configfile, "log_msgfile")

        # ------------------------
        # PROTOCOLS
        config.protocol_startup = bool(read_config(cmdarg.configfile, "protocol_startup") == "yes")
        config.protocol_file = read_config(cmdarg.configfile, "protocol_file")

    else:
        # config file not found, set default values
        log_me('error', "Configuration file not found (" + cmdarg.configfile + ") Line: " + _line())

# ----------------------------------------------------------------------------

def open_serialport():
    """
    Open serial port for communication to the RFXtrx device.
    """

    # Check that serial module is loaded
    try:
        log_me('debug', "Serial extension version: " + VERSION)
    except Exception, err:
        log_me('error', "You need to install Serial extension for Python")
        log_me('error', err)
        exit(1)

    # Check for serial device
    if config.device:
        log_me('debug', "Device: " + config.device)
    else:
        log_me('error', "Device name missing. Line: " + _line())
        exit(1)

    # Open serial port
    log_me('debug', "Open Serialport")
    try:
        serial_param.port = Serial(config.device,
                                   serial_param.rate,
                                   timeout=serial_param.timeout)
    except SerialException, err:
        log_me('error', "Failed to connect on device " + config.device + " Line: " + _line())
        log_me('error', err)
        exit(1)

    if not serial_param.port.isOpen():
        serial_param.port.open()

# ----------------------------------------------------------------------------

def close_serialport():
    """
    Close serial port.
    """

    log_me('debug', "Close serial port")
    try:
        serial_param.port.close()
        log_me('debug', "Serial port closed")
    except SerialException, err:
        log_me('error', "Failed to close the serial port (" + config.device + ") Line: " + _line())
        log_me('error', err)
        exit(1)

# ----------------------------------------------------------------------------

def logger_init(configfile, name, debug):
    """

    Init loghandler and logging

    Input:

        - configfile = location of the config.xml
        - name = name
        - debug = True will send log to stdout, False to file

    Output:

        - Returns logger handler
        - In case of no configfile found, return False

    """
    program_path = os.path.dirname(os.path.realpath(__file__))
    dom = None

    if os.path.exists(os.path.join(program_path, configfile)):

        # Read config file
        config_file = open(os.path.join(program_path, configfile), 'r')
        data = config_file.read()
        config_file.close()

        try:
            dom = minidom.parseString(data)
        except Exception, err:
            log_me('error', "problem in the %s file, cannot process it" % str(configfile))
            log_me('error', err)
            return False

        if dom:

            formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s')

            # Get loglevel from config file
            try:
                xml_tag = dom.getElementsByTagName('loglevel')[0].toxml()
                loglevel = xml_tag.replace('<loglevel>', '').replace('</loglevel>', '')
                loglevel = loglevel.upper()
            except Exception, err:
                loglevel = "ERROR"
                log_me('warning', err)

            # Get logfile from config file
            try:
                xml_tag = dom.getElementsByTagName('logfile')[0].toxml()
                logfile = xml_tag.replace('<logfile>', '').replace('</logfile>', '')
            except Exception, err:
                logfile = None
                log_me('warning', err)

            if debug:
                loglevel = "DEBUG"
                handler = StreamHandler()
                handler.setFormatter(formatter)
                logger = getLogger(name)
                logger.setLevel(getLevelName(loglevel))
                logger.addHandler(handler)

            if logfile:
                handler = FileHandler(logfile)
                handler.setFormatter(formatter)
                logger = getLogger(name)
                logger.setLevel(getLevelName(loglevel))
                logger.addHandler(handler)

            return logger

    else:
        log_me('error', "Cannot find configuration file (%s)" % str(configfile))
        return False

def output_me(timestamp, message, packettype, subtype, seqnbr, metadata_list):
    """
    This function writes json or csv output in a different file
    """ 
    output_file = open('/var/log/output.log', 'a+')

    rawcmd = ByteToHex(message)
    rawcmd = rawcmd.replace(' ', '')

    if cmdarg.printout_csv:
        result = "%s;%s;%s;%s;%s" % (timestamp, rawcmd, packettype, subtype, seqnbr)
        for metadata in metadata_list:
            result += ";%s" % metadata[1]
    else:
        result = dict()
        result['timestamp'] = timestamp
        result['rawcmd'] = rawcmd
        result['packettype'] = rfx.rfx_packettype[packettype]
        result['packettype_id'] = packettype
        result['subtype'] = subtype
        result['seqnbr'] = seqnbr
        result['metadata'] = dict()
        for metadata in metadata_list:
            result['metadata'][metadata[0]] = metadata[1]
        result = dumps(result)
    output_file.write(str(result) + "\n")
    output_file.close()
    sys.stdout.write(str(result) + "\n")
    sys.stdout.flush()


def log_me(verbosity, message):
    """
    This function write logs
    """
    if verbosity == 'error':
        logger.error(message)
    elif verbosity == 'warning':
        logger.warning(message)
    elif verbosity == 'info':
        if cmdarg.printout_complete:
            logger.info(message)
    else:
        if cmdarg.printout_debug:
            logger.debug(message)

# ----------------------------------------------------------------------------

def main():

    global logger

    # Get directory of the rfxcmd script
    config.program_path = os.path.dirname(os.path.realpath(__file__))

    parser = OptionParser()
    parser.add_option("-d", "--device", action="store", type="string", dest="device", \
        help="The serial device of the RFXCOM, example /dev/ttyUSB0")
    parser.add_option("-l", "--listen", action="store_true", dest="listen", \
        help="Listen for messages from RFX device")
    parser.add_option("-x", "--simulate", action="store", type="string", dest="simulate", \
        help="Simulate one incoming data message")
    parser.add_option("-s", "--sendmsg", action="store", type="string", dest="sendmsg", \
        help="Send one message to RFX device")
    parser.add_option("-f", "--rfxstatus", action="store_true", dest="rfxstatus", \
        help="Get RFX device status")
    parser.add_option("-o", "--config", action="store", type="string", dest="config", \
        help="Specify the configuration file")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, \
        help="Output all messages to stdout")
    parser.add_option("-c", "--csv", action="store_true", dest="csv", default=False, \
        help="Output all messages to stdout in CSV format")
    parser.add_option("-V", "--version", action="store_true", dest="version", \
        help="Print rfxcmd version information")
    parser.add_option("-D", "--debug", action="store_true", dest="debug", default=False, \
        help="Debug printout on stdout")
    parser.add_option("--listprotocol", action="store_true", dest="listprotocol", default=False, \
        help="List protocol settings")
    (options, _) = parser.parse_args()

    # ----------------------------------------------------------
    # VERSION PRINT
    if options.version:
        print_version()

    # ----------------------------------------------------------
    # CONFIG FILE
    if options.config:
        cmdarg.configfile = options.config
    else:
        cmdarg.configfile = os.path.join(config.program_path, "config.xml")

    # ----------------------------------------------------------
    # LOGHANDLER
    logger = logger_init(cmdarg.configfile, 'rfxcmd', True)
    cmdarg.printout_debug = False
    cmdarg.printout_complete = False

    if options.debug:
        cmdarg.printout_debug = True
        cmdarg.printout_complete = True
        log_me('debug', "Debug printout " + _line())

    if options.verbose:
        cmdarg.printout_complete = True
        log_me('info', "Verbose printout " + _line())
        log_me('info', "RFXCMD Version " + __version__)

    if not logger:
        log_me('error', "Cannot find configuration file (%s)" % cmdarg.configfile)
        exit(1)

    log_me('debug', "Python version: %s.%s.%s" % sys.version_info[:3])
    log_me('debug', "RFXCMD Version: " + __version__)
    log_me('debug', __date__.replace('$', ''))

    # ----------------------------------------------------------
    # PROCESS CONFIG.XML
    log_me('debug', "Configfile: " + cmdarg.configfile)
    log_me('debug', "Read configuration file")
    read_configfile()

    # ----------------------------------------------------------
    # OUTPUTOUTPUT
    if options.csv:
        log_me('debug', "CSV printout")
        cmdarg.printout_csv = True
    else:
        cmdarg.printout_csv = False

    # ----------------------------------------------------------
    # Print protocol list
    if options.listprotocol:
        log_me('debug', "List protocol file to screen")
        protocol.print_protocolfile(config.protocol_file)

    # ----------------------------------------------------------
    # WHITELIST
    if config.whitelist_active:
        log_me('debug', "Read whitelist file")
        read_whitelistfile()

    # ----------------------------------------------------------
    # Triggerlist
    if config.trigger_active:
        log_me('debug', "Read triggerlist file")
        read_triggerfile()

    # ----------------------------------------------------------
    # SERIAL
    if options.device:
        config.device = options.device
    elif config.serial_device:
        config.device = config.serial_device
    else:
        config.device = None

    # ----------------------------------------------------------
    # DAEMON
    if config.daemon_active and options.listen:
        log_me('debug', "Daemon")
        log_me('debug', "Check PID file")

        if config.daemon_pidfile:
            cmdarg.pidfile = config.daemon_pidfile
            cmdarg.createpid = True
            log_me('debug', "PID file '" + cmdarg.pidfile + "'")

            if os.path.exists(cmdarg.pidfile):
                log_me('info', "PID file '" + cmdarg.pidfile + "' already exists. Exiting.")
                log_me('debug', "PID file '" + cmdarg.pidfile + "' already exists.")
                exit(1)
            else:
                log_me('debug', "PID file does not exists")

        else:
            log_me('error', "Command argument --pidfile missing. Line: " + _line())
            exit(1)

        log_me('debug', "Check platform")
        if sys.platform == 'win32':
            log_me('error', "Daemonize not supported under Windows. Line: " + _line())
            exit(1)
        else:
            log_me('debug', "Platform: " + sys.platform)

            try:
                log_me('debug', "Write PID file")
                file(cmdarg.pidfile, 'w').write("pid\n")
            except IOError, err:
                log_me('error', "Line: " + _line())
                log_me('error', "Unable to write PID file: %s [%d]" % (err.strerror, err.errno))
                raise SystemExit("Unable to write PID file: %s [%d]" % (err.strerror, err.errno))

            log_me('debug', "Deactivate screen printouts")
            cmdarg.printout_complete = False

            log_me('debug', "Start daemon")
            daemonize()

    # ----------------------------------------------------------
    # SIMULATE
    if options.simulate:
        option_simulate(options.simulate)

    # ----------------------------------------------------------
    # LISTEN
    if options.listen:
        option_listen()

    # ----------------------------------------------------------
    # SEND MESSAGE
    if options.sendmsg:
        cmdarg.rawcmd = options.sendmsg
        option_send()

    # ----------------------------------------------------------
    # GET RFX STATUS
    if options.rfxstatus:
        cmdarg.rawcmd = rfxcmd.status
        option_send()

    log_me('debug', "Exit 0")
    exit(0)

# ------------------------------------------------------------------------------

if __name__ == '__main__':

    # Init shutdown handler
    signal(SIGINT, handler)
    signal(SIGTERM, handler)

    # Init objects
    config = ConfigData()
    cmdarg = CmdArgData()
    rfx = lib.rfx_sensors.rfx_data()
    rfxcmd = RfxCmdData()
    serial_param = SerialData()

    # Triggerlist
    triggerlist = TriggerData()

    # Whitelist
    whitelist = WhitelistData()

    # Check python version
    check_pythonversion()

    main()

# ------------------------------------------------------------------------------
# END
# ------------------------------------------------------------------------------
