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
__version__ = "1.0.0"
__maintainer__ = "Nicolas Béguier"
__date__ = "$Date: 2018-12-27 14:05:33 +0100 (Thu, 27 Dec 2018) $"

# Standard library
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

# 3rd party library
# These might not be needed, depended on usage
from serial import Serial, VERSION, SerialException

# Debug
# from pdb import set_trace as st

# RFXCMD library
from lib.rfx_socket import MESSAGEQUEUE, RFXcmdSocketAdapter
from lib.rfx_utils import stripped, ByteToHex
import lib.rfx_sensors
import lib.rfx_decode_0x0 as rfxdecode0x0
import lib.rfx_decode_0x1 as rfxdecode0x1
import lib.rfx_decode_0x2 as rfxdecode0x2
import lib.rfx_decode_0x3 as rfxdecode0x3
import lib.rfx_decode_0x4 as rfxdecode0x4
import lib.rfx_decode_0x5 as rfxdecode0x5
import lib.rfx_decode_0x7 as rfxdecode0x7
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

    if packettype == '14' and len(message) != 11:
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

    if packettype == '30' and len(message) != 8:
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

    metadata = list()
    output_extra = list()

    # 0x0 - Interface Control
    if packettype == '00':
        log_me('debug', "Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

    # 0x01 - Interface Message
    if packettype == '01':
        decoded = True
        metadata, output_extra = rfxdecode0x0.decode_0x01(message)

    # 0x02 - Receiver/Transmitter Message
    if packettype == '02':
        decoded = True
        metadata, output_extra = rfxdecode0x0.decode_0x02(subtype, seqnbr, id1)

    # 0x03 - Undecoded Message
    if packettype == '03':
        decoded = True
        metadata, output_extra = rfxdecode0x0.decode_0x03(message, subtype, seqnbr)

    # 0x10 Lighting1
    if packettype == '10':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x10(message, subtype, seqnbr)

    # 0x11 Lighting2
    if packettype == '11':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x11(message, subtype, seqnbr)

    # 0x12 Lighting3
    if packettype == '12':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x12(message, subtype, seqnbr)

    # 0x13 Lighting4
    if packettype == '13':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x13(message, subtype, seqnbr)

    # 0x14 Lighting5
    if packettype == '14':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x14(message, subtype, seqnbr, id1, id2)

    # 0x15 Lighting6
    if packettype == '15':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x15(message, subtype, seqnbr, id1, id2)

    # 0x16 Chime
    if packettype == "16":
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x16(message, subtype, seqnbr, id1, id2)

    # 0x17 Fan (Transmitter only)
    if packettype == '17':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x17(subtype, seqnbr)

    # 0x18 Curtain1 (Transmitter only)
    if packettype == '18':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x18(subtype, seqnbr)

    # 0x19 Blinds1
    if packettype == '19':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x19(subtype, seqnbr)

    # 0x1A RTS
    if packettype == '1A':
        decoded = True
        metadata, output_extra = rfxdecode0x1.decode_0x1a(message, subtype, seqnbr, id1, id2)

    # 0x20 Security1
    if packettype == '20':
        decoded = True
        metadata, output_extra = rfxdecode0x2.decode_0x20(message, subtype, seqnbr, id1, id2)

    # 0x28 Camera1
    if packettype == '28':
        decoded = True
        metadata, output_extra = rfxdecode0x2.decode_0x28(subtype, seqnbr)

    # 0x30 Remote control and IR
    if packettype == '30':
        decoded = True
        metadata, output_extra = rfxdecode0x3.decode_0x30(message, subtype, seqnbr, id1)

    # 0x40 Thermostat1
    if packettype == '40':
        decoded = True
        metadata, output_extra = rfxdecode0x4.decode_0x40(message, subtype, seqnbr, id1, id2)

    # 0x41 Thermostat2
    if packettype == '41':
        decoded = True
        metadata, output_extra = rfxdecode0x4.decode_0x41(subtype, seqnbr)

    # 0x42 Thermostat3
    if packettype == '42':
        decoded = True
        metadata, output_extra = rfxdecode0x4.decode_0x42(message, subtype, seqnbr, id1, id2)

    # 0x50 Temperature sensors
    if packettype == '50':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x50(message, subtype, seqnbr, id1, id2)

    # 0x51 Humidity sensors
    if packettype == '51':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x51(message, subtype, seqnbr, id1, id2)

    # 0x52 Temperature and humidity sensors
    if packettype == '52':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x52(message, subtype, seqnbr, id1, id2)

    # 0x53 Barometric
    if packettype == '53':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x53(subtype, seqnbr)

    # 0x54 Temperature, humidity and barometric sensors
    if packettype == '54':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x54(message, subtype, seqnbr, id1, id2, \
            config.barometric)

    # 0x55 Rain sensors
    if packettype == '55':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x55(message, subtype, seqnbr, id1, id2)

    # 0x56 Wind sensors
    if packettype == '56':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x56(message, subtype, seqnbr, id1, id2)

    # 0x57 UV Sensor
    if packettype == '57':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x57(message, subtype, seqnbr, id1, id2)

    # 0x58 Date/Time sensor
    if packettype == '58':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x58(message, subtype, seqnbr, id1, id2)

    # 0x59 Current Sensor
    if packettype == '59':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x59(message, subtype, seqnbr, id1, id2)

    # 0x5A Energy sensor
    if packettype == '5A':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x5a(message, subtype, seqnbr, id1, id2)

    # 0x5B Current Sensor
    if packettype == '5B':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x5b(message, subtype, seqnbr, id1, id2)

    # 0x5C Power Sensors
    if packettype == '5C':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x5c(message, subtype, seqnbr, id1, id2)

    # 0x5D
    if packettype == '5D':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x5d(subtype, seqnbr)

    # 0x5E Gas Usage Sensor
    if packettype == '5E':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x5e(subtype, seqnbr)

    # 0x5F Water Usage Sensor
    if packettype == '5F':
        decoded = True
        metadata, output_extra = rfxdecode0x5.decode_0x5f(subtype, seqnbr)

    # 0x70 RFXsensor
    if packettype == '70':
        decoded = True
        metadata, output_extra = rfxdecode0x7.decode_0x70(message, subtype, seqnbr, id1)

    # 0x71 RFXmeter
    if packettype == '71':
        decoded = True
        metadata, output_extra = rfxdecode0x7.decode_0x71(message, subtype, seqnbr, id1, id2)

    # 0x72 FS20
    if packettype == '72':
        decoded = True
        metadata, output_extra = rfxdecode0x7.decode_0x72(subtype, seqnbr)

    # Not decoded message

    # The packet is not decoded, then log_me('info', it on the screen)
    if not decoded:
        log_me('error', "Message not decoded. Line: " + _line())
        log_me('error', "Message: " + ByteToHex(message))
        log_me('info', timestamp + " " + ByteToHex(message))
        log_me('info', "RFXCMD cannot decode message, see http://code.google.com/p/rfxcmd/wiki/")

    # Print result
    print_decoded(metadata)
    output_me(timestamp, message, packettype, subtype, seqnbr, output_extra)

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
    except TypeError, err:
        log_me('error', "Packet not hex format")
        log_me('error', err)
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
    except TypeError, err:
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
    except ValueError, err:
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

def print_decoded(metadata, prefix=""):
    """
    Display metadata of a list of dict which may contains metadata as value
    """
    for i in metadata:
        if isinstance(i['value'], list):
            log_me('info', '%s%s:' % (prefix, i['key']))
            print_decoded(i['value'], prefix="    ")
        elif 'unit' in i:
            log_me('info', '%s%s: %s %s' % (prefix, i['key'], i['value'], i['unit']))
        else:
            log_me('info', '%s%s: %s' % (prefix, i['key'], i['value']))

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

    # Whitelist
    whitelist = WhitelistData()

    # Check python version
    check_pythonversion()

    main()

# ------------------------------------------------------------------------------
# END
# ------------------------------------------------------------------------------
