#!/usr/bin/env python3
# coding=UTF-8
"""
# ------------------------------------------------------------------------------
#
#   RFXPROTO.PY
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
#   Website: http://code.google.com/p/rfxcmd/
#
#   $Rev: 566 $
#   $Date: 2013-11-22 21:43:41 +0100 (Fri, 22 Nov 2013) $
#
#   NOTES
#
#   RFXCOM is a Trademark of RFSmartLink.
#
# ------------------------------------------------------------------------------
#
# Protocol License Agreement
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
"""

__author__ = "Sebastian Sjoholm"
__copyright__ = "Copyright 2012-2014, Sebastian Sjoholm"
__license__ = "GPL"
__version__ = "2.0.0"
__maintainer__ = "Nicolas Béguier"
__date__ = "$Date: 2019-06-12 08:05:33 +0100 (Thu, 12 Jun 2019) $"

# Default modules
from codecs import decode as codecs_decode
import logging
import sys
import optparse
import time
import binascii
import traceback

# Serial
try:
    import serial
except ImportError as err:
    print(err)
    sys.exit(1)

# Debug
# from pdb import set_trace as st

# RFXCMD library
from lib.rfx_utils import ByteToHex

# ------------------------------------------------------------------------------
class rfxcmd_data:
    def __init__(
            self,
            reset="0d00000000000000000000000000",
            status="0d00000002000000000000000000",
            save="0d00000006000000000000000000"
        ):
        self.reset = reset
        self.status = status
        self.save = save

class serial_data:
    def __init__(
            self,
            device=None,
            port=None,
            rate=38400,
            timeout=9
        ):
        self.device = device
        self.port = port
        self.rate = rate
        self.timeout = timeout

# ------------------------------------------------------------------------------

"""
Bit manipulation
Source: http://wiki.python.org/moin/BitManipulation
"""

def testBit(int_type, offset):
    mask = 1 << offset
    return int_type & mask
    
def setBit(int_type, offset):
    mask = 1 << offset
    return int_type | mask

def clearBit(int_type, offset):
    mask = ~(1 << offset)
    return int_type & mask

def toggleBit(int_type, offset):
    mask = 1 << offset
    return int_type ^ mask

# ------------------------------------------------------------------------------
def print_version():
    """
    Print version information
    """
    print("RFXPROTO Version: {}".format(__version__))
    print(__date__.replace("$", ""))
    return

# ------------------------------------------------------------------------------
def readbytes(number):
    """
    Read amount of bytes from serial device
    """
    buf = bytes()
    for _ in range(number):
        try:
            byte = SERIAL.device.read()
        except IOError as err:
            LOGGER.error(err)
            return False
        except OSError as err:
            LOGGER.error(err)
            return False
        buf += byte
    return buf

# ------------------------------------------------------------------------------
def rfx_setmode(protocol, state):
    """
    Create setmode message
    """

    LOGGER.debug("Send status message")
    res = None
    try:
        res = rfx_sendmsg(RFXCMD.status)
        LOGGER.debug("Result: %s", str(res))
    except Exception as err:
        LOGGER.error(err)
        raise

    LOGGER.debug("Result: %s", str(ByteToHex(res)))

    if res:
        LOGGER.debug("Decode result")
        try:
            bstr = rfx_decode(res)
            LOGGER.debug("Result: %s", str(bstr))
        except Exception as err:
            LOGGER.error(err)
            raise

        LOGGER.debug("Binary: %s" % str(bstr))

        # Change
        bstr[protocol] = str(state)
        LOGGER.debug("Binary: " % str(bstr))

        # Complete message
        msg3 = bstr[0] + bstr[1] + bstr[2] + bstr[3] + bstr[4] + bstr[5] + bstr[6] + bstr[7]
        msg3_int = int(msg3, 2)
        msg3_hex = hex(msg3_int)[2:].zfill(2)
        msg4 = bstr[8] + bstr[9] + bstr[10] + bstr[11] + bstr[12] + bstr[13] + bstr[14] + bstr[15]
        msg4_int = int(msg4, 2)
        msg4_hex = hex(msg4_int)[2:].zfill(2)
        msg5 = bstr[16] + bstr[17] + bstr[18] + bstr[19] + bstr[20] + bstr[21] + bstr[22] + bstr[23]
        msg5_int = int(msg5, 2)
        msg5_hex = hex(msg5_int)[2:].zfill(2)
        LOGGER.debug("msg3: %s / %s" % (str(msg3), msg3_hex))
        LOGGER.debug("msg4: %s / %s" % (str(msg4), msg4_hex))
        LOGGER.debug("msg5: %s / %s" % (str(msg5), msg5_hex))

        # Send command
        command = "0D000000035300%s%s%s00000000" % (msg3_hex, msg4_hex, msg5_hex)
        LOGGER.debug("Command: %s" % command.upper())
        try:
            rfx_decodestatus(rfx_sendmsg(command.upper()))
        except Exception as err:
            LOGGER.error(err)
            raise

        return True
    LOGGER.error("Invalid result received")
    return False

# ------------------------------------------------------------------------------
def rfx_decode(message):
    """
    Decode RFX message and output the protocol part in a binary string list
    """

    LOGGER.debug("RFX_Encode -> BinStr")

    data = {\
        'packetlen' : ByteToHex(message[0]),\
        'packettype' : ByteToHex(message[1]),\
        'subtype' : ByteToHex(message[2]),\
        'seqnbr' : ByteToHex(message[3]),\
        'cmnd' : ByteToHex(message[4]),\
        'msg1' : ByteToHex(message[5]),\
        'msg2' : ByteToHex(message[6]),\
        'msg3' : ByteToHex(message[7]),\
        'msg4' : ByteToHex(message[8]),\
        'msg5' : ByteToHex(message[9]),\
        'msg6' : ByteToHex(message[10]),\
        'msg7' : ByteToHex(message[11]),\
        'msg8' : ByteToHex(message[12]),\
        'msg9' : ByteToHex(message[13])}

    LOGGER.debug("Extract the protocol part")

    try:
        msg3_bin = binascii.a2b_hex(data['msg3'])
        msg3_binstr = "".join("{:08b}".format(ord(i)) for i in msg3_bin)
    except Exception as err:
        LOGGER.error(err)
        raise

    LOGGER.debug("msg3_bin: %s", str(msg3_bin))
    LOGGER.debug("msg3_binstr: %s", str(msg3_binstr))

    msg4_bin = binascii.a2b_hex(data['msg4'])
    msg4_binstr = "".join("{:08b}".format(ord(i)) for i in msg4_bin)
    msg5_bin = binascii.a2b_hex(data['msg5'])
    msg5_binstr = "".join("{:08b}".format(ord(i)) for i in msg5_bin)

    return list(msg3_binstr + msg4_binstr + msg5_binstr)

# ------------------------------------------------------------------------------
def rfx_decodestatus(message):
    LOGGER.debug("Decode status message")

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

    LOGGER.info("RFX protocols")
    LOGGER.info("-------------------------------------------------------------------")
    LOGGER.info("#\tProtocol\t\t\tState")
    LOGGER.info("-------------------------------------------------------------------")

    # MSG 3

    if testBit(int(data['msg3'], 16), 7) == 128:
        LOGGER.info("0\tUndecoded\t\t\tEnabled")
    else:
        LOGGER.info("0\tUndecoded\t\t\tDisabled")

    if testBit(int(data['msg3'], 16), 6) == 64:
        LOGGER.info("1\tRFU\t\t\t\tEnabled")
    else:
        LOGGER.info("1\tRFU\t\t\t\tDisabled")

    if testBit(int(data['msg3'], 16), 5) == 32:
        LOGGER.info("2\tByrox SX\t\t\tEnabled")
    else:
        LOGGER.info("2\tByrox SX\t\t\tDisabled")

    if testBit(int(data['msg3'], 16), 4) == 16:
        LOGGER.info("3\tRSL\t\t\t\tEnabled")
    else:
        LOGGER.info("3\tRSL\t\t\t\tDisabled")

    if testBit(int(data['msg3'], 16), 3) == 8:
        LOGGER.info("4\tLightning4\t\t\tEnabled")
    else:
        LOGGER.info("4\tLightning4\t\t\tDisabled")

    if testBit(int(data['msg3'], 16), 2) == 4:
        LOGGER.info("5\tFineOffset/Viking\t\tEnabled")
    else:
        LOGGER.info("5\tFineOffset/Viking\t\tDisabled")

    if testBit(int(data['msg3'], 16), 1) == 2:
        LOGGER.info("6\tRubicson\t\t\tEnabled")
    else:
        LOGGER.info("6\tRubicson\t\t\tDisabled")

    if testBit(int(data['msg3'], 16), 0) == 1:
        LOGGER.info("7\tAE Blyss\t\t\tEnabled")
    else:
        LOGGER.info("7\tAE Blyss\t\t\tDisabled")

    # MSG 4
    if testBit(int(data['msg4'], 16), 6) == 128:
        LOGGER.info("8\tBlindsT1/T2/T3/T4\t\tEnabled")
    else:
        LOGGER.info("8\tBlindsT1/T2/T3/T4\t\tDisabled")

    if testBit(int(data['msg4'], 16), 6) == 64:
        LOGGER.info("9\tBlindsT0\t\t\tEnabled")
    else:
        LOGGER.info("9\tBlindsT0\t\t\tDisabled")

    if testBit(int(data['msg4'], 16), 5) == 32:
        LOGGER.info("10\tProGuard\t\t\tEnabled")
    else:
        LOGGER.info("10\tProGuard\t\t\tDisabled")

    if testBit(int(data['msg4'], 16), 4) == 16:
        LOGGER.info("11\tFS20\t\t\t\tEnabled")
    else:
        LOGGER.info("11\tFS20\t\t\t\tDisabled")

    if testBit(int(data['msg4'], 16), 3) == 8:
        LOGGER.info("12\tLa Crosse\t\t\tEnabled")
    else:
        LOGGER.info("12\tLa Crosse\t\t\tDisabled")

    if testBit(int(data['msg4'], 16), 2) == 4:
        LOGGER.info("13\tHideki/UPM\t\t\tEnabled")
    else:
        LOGGER.info("13\tHideki/UPM\t\t\tDisabled")

    if testBit(int(data['msg4'], 16), 1) == 2:
        LOGGER.info("14\tAD LightwaveRF\t\t\tEnabled")
    else:
        LOGGER.info("14\tAD LightwaveRF\t\t\tDisabled")

    if testBit(int(data['msg4'], 16), 0) == 1:
        LOGGER.info("15\tMertik\t\t\t\tEnabled")
    else:
        LOGGER.info("15\tMertik\t\t\t\tDisabled")

    # MSG 5
    if testBit(int(data['msg5'], 16), 6) == 128:
        LOGGER.info("16\tBlindsT1/T2/T3/T4\t\tEnabled")
    else:
        LOGGER.info("16\tBlindsT1/T2/T3/T4\t\tDisabled")

    if testBit(int(data['msg5'], 16), 6) == 64:
        LOGGER.info("17\tBlindsT0\t\t\tEnabled")
    else:
        LOGGER.info("17\tBlindsT0\t\t\tDisabled")

    if testBit(int(data['msg5'], 16), 5) == 32:
        LOGGER.info("18\tOregon Scientific\t\tEnabled")
    else:
        LOGGER.info("18\tOregon Scientific\t\tDisabled")

    if testBit(int(data['msg5'], 16), 4) == 16:
        LOGGER.info("19\tMeiantech\t\t\tEnabled")
    else:
        LOGGER.info("19\tMeiantech\t\t\tDisabled")

    if testBit(int(data['msg5'], 16), 3) == 8:
        LOGGER.info("20\tHomeEasy EU\t\t\tEnabled")
    else:
        LOGGER.info("20\tHomeEasy EU\t\t\tDisabled")

    if testBit(int(data['msg5'], 16), 2) == 4:
        LOGGER.info("21\tAC\t\t\t\tEnabled")
    else:
        LOGGER.info("21\tAC\t\t\t\tDisabled")

    if testBit(int(data['msg5'], 16), 1) == 2:
        LOGGER.info("22\tARC\t\t\t\tEnabled")
    else:
        LOGGER.info("22\tARC\t\t\t\tDisabled")

    if testBit(int(data['msg5'], 16), 0) == 1:
        LOGGER.info("23\tX10\t\t\t\tEnabled")
    else:
        LOGGER.info("23\tX10\t\t\t\tDisabled")

    return

# ------------------------------------------------------------------------------
def rfx_sendmsg(message=None):

    if message is None:
        LOGGER.debug("No message was specified")
        return False

    # Check that serial module is loaded
    try:
        LOGGER.debug("Serial extension version: " + serial.VERSION)
    except:
        LOGGER.error("Error: Serial extension for Python could not be loaded")
        return False

    # Check for serial device
    if SERIAL.port:
        LOGGER.debug("Device: " + SERIAL.port)
    else:
        LOGGER.error("Device name missing")
        return False

    # Open serial port
    LOGGER.debug("Open Serialport")
    try:
        SERIAL.device = serial.Serial(SERIAL.port, SERIAL.rate, timeout=SERIAL.timeout)
    except serial.SerialException as err:
        LOGGER.error("Error: Failed to connect on device, %s" % err)
        return False

    # Flush buffer
    LOGGER.debug("Serialport flush output")
    SERIAL.device.flushOutput()
    LOGGER.debug("Serialport flush input")
    SERIAL.device.flushInput()

    # Send RESET
    LOGGER.debug("Send RFX reset")
    SERIAL.device.write(codecs_decode(RFXCMD.reset, "hex"))
    time.sleep(1)

    # Flush buffer
    LOGGER.debug("Serialport flush output")
    SERIAL.device.flushOutput()
    LOGGER.debug("Serialport flush input")
    SERIAL.device.flushInput()

    LOGGER.debug("Send message")
    SERIAL.device.write(codecs_decode(message, "hex"))
    time.sleep(1)

    # Waiting reply
    result = None
    byte = None
    LOGGER.debug("Wait for the reply")
    try:
        while 1:
            time.sleep(0.01)
            try:
                try:
                    if SERIAL.device.inWaiting() != 0:
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                        LOGGER.debug("Timestamp: %s", timestamp)
                        LOGGER.debug("SerWaiting: %d", SERIAL.device.inWaiting())
                        byte = SERIAL.device.read()
                        LOGGER.debug("Byte: %s", ByteToHex(byte))
                except IOError as err:
                    LOGGER.error("Serial read error: %s", err)
                    break

                try:
                    if byte is not None:
                        if ord(byte) == 20 or ord(byte) == 13:
                            result = byte + readbytes(ord(byte))
                            LOGGER.debug("Message: %s", ByteToHex(result))
                            break
                        else:
                            result = byte + readbytes(ord(byte))
                            LOGGER.debug("Message: %s", ByteToHex(result))
                            LOGGER.error("Wrong or no response received")
                            sys.exit(1)

                except Exception as err:
                    LOGGER.error(err)
                    sys.exit(1)

            except OSError as err:
                LOGGER.error("Error in message: %s", ByteToHex(message))
                LOGGER.error(err)
                LOGGER.error("Traceback: %s", traceback.format_exc())
                LOGGER.error("Serial error (%s) ", ByteToHex(message))
                break

    except KeyboardInterrupt:
        LOGGER.debug("Received keyboard interrupt")
        pass

    LOGGER.debug("Close serial port")
    try:
        SERIAL.device.close()
        LOGGER.debug("Serial port closed")
    except:
        LOGGER.error("Error: Failed to close the serial port (%s)" % SERIAL.port)
        return False

    return result

# ------------------------------------------------------------------------------
if __name__ == '__main__':

    RFXCMD = rfxcmd_data()
    SERIAL = serial_data()

    PARSER = optparse.OptionParser()
    PARSER.add_option("-d", "--device", action="store", type="string", dest="device", help="Serial device of the RFXtrx433")
    PARSER.add_option("-l", "--list", action="store_true", dest="list", help="List all protocols")
    PARSER.add_option("-p", "--protocol", action="store", type="string", dest="protocol", help="Protocol number")
    PARSER.add_option("-s", "--setstate", action="store", type="string", dest="state", help="Set protocol state (on or off)")
    PARSER.add_option("-v", "--save", action="store_true", dest="save", help="Save current settings in device (Note device have limited write cycles)")
    PARSER.add_option("-V", "--version", action="store_true", dest="version", help="Print rfxcmd version information")
    PARSER.add_option("-D", "--debug", action="store_true", dest="debug", help="Debug logging on screen")

    (OPTIONS, ARGS) = PARSER.parse_args()

    if OPTIONS.debug:
        LOGLEVEL = logging.DEBUG
    else:
        LOGLEVEL = logging.ERROR

    # Logging
    FORMATTER = logging.Formatter('%(asctime)s - %(threadName)s - %(module)s:%(lineno)d - %(levelname)s - %(message)s')
    HANDLER = logging.StreamHandler()
    HANDLER.setFormatter(FORMATTER)
    LOGGER = logging.getLogger("RFXPROTO")
    LOGGER.setLevel(LOGLEVEL)
    LOGGER.addHandler(HANDLER)

    LOGGER.debug("Logger started")
    LOGGER.debug("Version: %s", __version__)
    LOGGER.debug("Date: %s", __date__.replace('$', ''))

    if OPTIONS.version:
        LOGGER.debug("Print version")
        print_version()

    if OPTIONS.device:
        SERIAL.port = OPTIONS.device
        LOGGER.debug("Serial device: %s", SERIAL.port)
    else:
        SERIAL.port = None
        LOGGER.debug("Serial device: %s", SERIAL.port)

    # Set protocol state
    if OPTIONS.protocol:
        pnum = int(OPTIONS.protocol)
        if OPTIONS.state == "on" or OPTIONS.state == "off":
            if not SERIAL.port == None:
                LOGGER.debug("Protocol num: %s" % str(pnum))
                LOGGER.debug("Protocol state: %s" % OPTIONS.state)
                if OPTIONS.state == "on":
                    rfx_setmode(pnum, 1)
                else:
                    rfx_setmode(pnum, 0)
            else:
                LOGGER.error("Serial device is missing")
        else:
            LOGGER.error("Unknown state parameter for protocol")

    # Get current status
    if OPTIONS.list:
        if not SERIAL.port == None:
            LOGGER.debug("Get current state")
            try:
                RESULT = rfx_sendmsg(RFXCMD.status)
                LOGGER.debug("Result: %s" % ByteToHex(RESULT))
                if RESULT:
                    rfx_decodestatus(RESULT)
                else:
                    LOGGER.error("Invalid result received")
            except Exception as err:
                LOGGER.error("Send failed, error: {}".format(err))
        else:
            LOGGER.error("Serial device is missing")

    LOGGER.debug("Exit")
    sys.exit(0)

# ------------------------------------------------------------------------------
# END
# ------------------------------------------------------------------------------
