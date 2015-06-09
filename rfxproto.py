#!/usr/bin/python
# coding=UTF-8

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

__author__ = "Sebastian Sjoholm"
__copyright__ = "Copyright 2012-2014, Sebastian Sjoholm"
__license__ = "GPL"
__version__ = "0.1 (" + filter(str.isdigit, "$Rev: 566 $") + ")"
__maintainer__ = "Sebastian Sjoholm"
__email__ = "sebastian.sjoholm@gmail.com"
__status__ = "Development"
__date__ = "$Date: 2013-11-22 21:43:41 +0100 (Fri, 22 Nov 2013) $"

# Default modules
import logging
import sys
import string
import optparse
import time
import binascii
import fcntl

# Serial
try:
    import serial
except ImportError as err:
    print("Error: %s" % str(err))
    sys.exit(1)

# ------------------------------------------------------------------------------
class rfxcmd_data:
    def __init__(
        self,
        reset = "0d00000000000000000000000000",
        status = "0d00000002000000000000000000",
        save = "0d00000006000000000000000000"
        ):
        
        self.reset = reset
        self.status = status
        self.save = save

class serial_data:
    def __init__(
        self,
        device = None,
        port = None,
        rate = 38400,
        timeout = 9
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
    return(int_type & mask)
    
def setBit(int_type, offset):
    mask = 1 << offset
    return(int_type | mask)

def clearBit(int_type, offset):
    mask = ~(1 << offset)
    return(int_type & mask)

def toggleBit(int_type, offset):
    mask = 1 << offset
    return(int_type ^ mask)
    
# ------------------------------------------------------------------------------
def ByteToHex( byteStr ):
    """
    Convert a byte string to it's hex string representation e.g. for output.
    Added str() to byteStr in case input data is in integer
    Credit: http://code.activestate.com/recipes/510399-byte-to-hex-and-hex-to-byte-string-conversion/
    """
    return ''.join( [ "%02X " % ord( x ) for x in str(byteStr) ] ).strip()

# ------------------------------------------------------------------------------
def stripped(str):
    """
    Strip all characters that are not valid
    Credit: http://rosettacode.org/wiki/Strip_control_codes_and_extended_characters_from_a_string
    """
    return "".join([i for i in str if ord(i) in range(32, 127)])

# ------------------------------------------------------------------------------
def print_version():
    """
    Print version information
    """
    print "RFXPROTO Version: %s" % __version__
    print __date__.replace('$', '')
    return

# ------------------------------------------------------------------------------
def readbytes(number):
    """
    Read amount of bytes from serial device
    """
    buf = ''
    for i in range(number):
        try:
            byte = s.device.read()
        except IOError as err:
            print("Error: %s" % str(err))
            return False
        except OSError as err:
            print("Error: %s" % str(err))
            return False
        buf += byte
    return buf

# ------------------------------------------------------------------------------
def rfx_setmode(protocol, state):
    """
    Create setmode message
    """

    logger.debug("Send status message")
    result = None
    try:
        result = rfx_sendmsg(r.status)
        logger.debug("Result: %s", str(result))
    except Exception as err:
        logger.debug("Error: %s", str(err))
        print "Error: Could not send message: %s " % str(err)
        raise

    logger.debug("Result: %s", str(ByteToHex(result)))

    if result:

        logger.debug("Decode result") 
        try:
            bstr = rfx_decode(result)
            logger.debug("Result: %s", str(bstr))
        execpt Exception as err:
            logger.error("Error: %s", str(err))
            raise

        logger.debug("Binary: %s" % str(bstr))

        # Change
        bstr[protocol] = str(state)
        logger.debug("Binary: %s" % str(bstr))

        # Complete message
        msg3 = bstr[0] + bstr[1] + bstr[2] + bstr[3] + bstr[4] + bstr[5] + bstr[6] + bstr[7]
        msg3_int = int(msg3,2)
        msg3_hex = hex(msg3_int)[2:].zfill(2)
        msg4 = bstr[8] + bstr[9] + bstr[10] + bstr[11] + bstr[12] + bstr[13] + bstr[14] + bstr[15]
        msg4_int = int(msg4,2)
        msg4_hex = hex(msg4_int)[2:].zfill(2)
        msg5 = bstr[16] + bstr[17] + bstr[18] + bstr[19] + bstr[20] + bstr[21] + bstr[22] + bstr[23]
        msg5_int = int(msg5,2)
        msg5_hex = hex(msg5_int)[2:].zfill(2)
        logger.debug("msg3: %s / %s" % (str(msg3), msg3_hex))
        logger.debug("msg4: %s / %s" % (str(msg4), msg4_hex))
        logger.debug("msg5: %s / %s" % (str(msg5), msg5_hex))
        
        # Send command
        command = "0D000000035300%s%s%s00000000" % (msg3_hex, msg4_hex, msg5_hex)
        logger.debug("Command: %s" % command.upper())
        try:
            rfx_decodestatus(rfx_sendmsg(command.upper()))
        except Exception as err:
            logger.error("Error: %s", str(err))
            raise

        return True

    else:
        print("Invalid result received")
        return False

# ------------------------------------------------------------------------------
def rfx_decode(message):
    """
    Decode RFX message and output the protocol part in a binary string list
    """
    
    logger.debug("RFX_Encode -> BinStr")
    
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
    
    logger.debug("Extract the protocol part")
    
    try:
        msg3_bin = binascii.a2b_hex(data['msg3'])
        msg3_binstr = "".join("{:08b}".format(ord(i)) for i in msg3_bin)
    except Exception as err:
        logger.error("Error: %s", str(err))
        raise

    logger.debug("msg3_bin: %s", str(msg3_bin))
    logger.debug("msg3_binstr: %s", str(msg3_binstr))
    
    msg4_bin = binascii.a2b_hex(data['msg4'])
    msg4_binstr = "".join("{:08b}".format(ord(i)) for i in msg4_bin)
    msg5_bin = binascii.a2b_hex(data['msg5'])
    msg5_binstr = "".join("{:08b}".format(ord(i)) for i in msg5_bin)
    
    return list(msg3_binstr + msg4_binstr + msg5_binstr)

# ------------------------------------------------------------------------------
def rfx_decodestatus(message):
    
    logger.debug("Decode status message")
    
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
    
    print("RFX protocols")
    print("-------------------------------------------------------------------")
    print("#\tProtocol\t\t\tState")
    print("-------------------------------------------------------------------")
    
    # MSG 3
        
    if testBit(int(data['msg3'],16),7) == 128:
        print("0\tUndecoded\t\t\tEnabled")
    else:
        print("0\tUndecoded\t\t\tDisabled")
        
    if testBit(int(data['msg3'],16),6) == 64:
        print("1\tRFU\t\t\t\tEnabled")
    else:
        print("1\tRFU\t\t\t\tDisabled")
        
    if testBit(int(data['msg3'],16),5) == 32:
        print("2\tByrox SX\t\t\tEnabled")
    else:
        print("2\tByrox SX\t\t\tDisabled")
        
    if testBit(int(data['msg3'],16),4) == 16:
        print("3\tRSL\t\t\t\tEnabled")
    else:
        print("3\tRSL\t\t\t\tDisabled")
        
    if testBit(int(data['msg3'],16),3) == 8:
        print("4\tLightning4\t\t\tEnabled")
    else:
        print("4\tLightning4\t\t\tDisabled")
        
    if testBit(int(data['msg3'],16),2) == 4:
        print("5\tFineOffset/Viking\t\tEnabled")
    else:
        print("5\tFineOffset/Viking\t\tDisabled")
        
    if testBit(int(data['msg3'],16),1) == 2:
        print("6\tRubicson\t\t\tEnabled")
    else:
        print("6\tRubicson\t\t\tDisabled")
    
    if testBit(int(data['msg3'],16),0) == 1:
        print("7\tAE Blyss\t\t\tEnabled")
    else:
        print("7\tAE Blyss\t\t\tDisabled")
    
    # MSG 4
    if testBit(int(data['msg4'],16),6) == 128:
        print("8\tBlindsT1/T2/T3/T4\t\tEnabled")
    else:
        print("8\tBlindsT1/T2/T3/T4\t\tDisabled")
        
    if testBit(int(data['msg4'],16),6) == 64:
        print("9\tBlindsT0\t\t\tEnabled")
    else:
        print("9\tBlindsT0\t\t\tDisabled")
    
    if testBit(int(data['msg4'],16),5) == 32:
        print("10\tProGuard\t\t\tEnabled")
    else:
        print("10\tProGuard\t\t\tDisabled")
        
    if testBit(int(data['msg4'],16),4) == 16:
        print("11\tFS20\t\t\t\tEnabled")
    else:
        print("11\tFS20\t\t\t\tDisabled")
    
    if testBit(int(data['msg4'],16),3) == 8:
        print("12\tLa Crosse\t\t\tEnabled")
    else:
        print("12\tLa Crosse\t\t\tDisabled")
        
    if testBit(int(data['msg4'],16),2) == 4:
        print("13\tHideki/UPM\t\t\tEnabled")
    else:
        print("13\tHideki/UPM\t\t\tDisabled")
        
    if testBit(int(data['msg4'],16),1) == 2:
        print("14\tAD LightwaveRF\t\t\tEnabled")
    else:
        print("14\tAD LightwaveRF\t\t\tDisabled")
    
    if testBit(int(data['msg4'],16),0) == 1:
        print("15\tMertik\t\t\t\tEnabled")
    else:
        print("15\tMertik\t\t\t\tDisabled")
    
    # MSG 5
    if testBit(int(data['msg5'],16),6) == 128:
        print("16\tBlindsT1/T2/T3/T4\t\tEnabled")
    else:
        print("16\tBlindsT1/T2/T3/T4\t\tDisabled")
        
    if testBit(int(data['msg5'],16),6) == 64:
        print("17\tBlindsT0\t\t\tEnabled")
    else:
        print("17\tBlindsT0\t\t\tDisabled")
        
    if testBit(int(data['msg5'],16),5) == 32:
        print("18\tOregon Scientific\t\tEnabled")
    else:
        print("18\tOregon Scientific\t\tDisabled")
        
    if testBit(int(data['msg5'],16),4) == 16:
        print("19\tMeiantech\t\t\tEnabled")
    else:
        print("19\tMeiantech\t\t\tDisabled")
    
    if testBit(int(data['msg5'],16),3) == 8:
        print("20\tHomeEasy EU\t\t\tEnabled")
    else:
        print("20\tHomeEasy EU\t\t\tDisabled")
        
    if testBit(int(data['msg5'],16),2) == 4:
        print("21\tAC\t\t\t\tEnabled")
    else:
        print("21\tAC\t\t\t\tDisabled")
        
    if testBit(int(data['msg5'],16),1) == 2:
        print("22\tARC\t\t\t\tEnabled")
    else:
        print("22\tARC\t\t\t\tDisabled")
    
    if testBit(int(data['msg5'],16),0) == 1:
        print("23\tX10\t\t\t\tEnabled")
    else:
        print("23\tX10\t\t\t\tDisabled")
    
    return
    
# ------------------------------------------------------------------------------
def rfx_sendmsg(message=None):
    
    if message == None:
        logger.debug("No message was specified")
        return False
    
    # Check that serial module is loaded
    try:
        logger.debug("Serial extension version: " + serial.VERSION)
    except:
        logger.debug("Error: Serial extension for Python could not be loaded")
        print("Error: You need to install Serial extension for Python")
        return False
        
    # Check for serial device
    if s.port:
        logger.debug("Device: " + s.port)
    else:
        logger.error("Device name missing")
        print("Serial device is missing")
        return False
        
    # Open serial port
    logger.debug("Open Serialport")
    try:
        s.device = serial.Serial(s.port, s.rate, timeout=s.timeout)
    except serial.SerialException as err:
        logger.debug("Error: Failed to connect on device, %s" % str(err))
        print("Error: Failed to connect on device %s" % str(s.port))
        print("Error: %s" % str(err))
        return False
    
    # Flush buffer
    logger.debug("Serialport flush output")
    s.device.flushOutput()
    logger.debug("Serialport flush input")
    s.device.flushInput()

    # Send RESET
    logger.debug("Send RFX reset")
    s.device.write(r.reset.decode('hex'))
    time.sleep(1)

    # Flush buffer
    logger.debug("Serialport flush output")
    s.device.flushOutput()
    logger.debug("Serialport flush input")
    s.device.flushInput()
    
    logger.debug("Send message")
    s.device.write(message.decode('hex'))
    time.sleep(1)
    
    # Waiting reply
    result = None
    byte = None
    logger.debug("Wait for the reply")
    try:
        while 1:
            time.sleep(0.01)
            try:
                try:
                    if s.device.inWaiting() != 0:
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                        logger.debug("Timestamp: " + timestamp)
                        logger.debug("SerWaiting: " + str(s.device.inWaiting()))
                        byte = s.device.read()
                        logger.debug("Byte: " + str(ByteToHex(byte)))
                except IOError, err:
                    logger.error("Serial read error: %s" % str(err))
                    print("Serial error: " + str(err))
                    break
                
                try:
                    if byte is not None:
                        if ord(byte) == 13:
                            result = byte + readbytes( ord(byte) )
                            logger.debug("Message: " + str(ByteToHex(result)))
                            break
                        else:
                            logger.debug("Wrong message received")
                            result = byte + readbytes( ord(byte) )
                            logger.debug("Message: " + str(ByteToHex(result)))
                            print("Error: Wrong or no response received")
                            sys.exit(1)
                            
                except Exception as err:
                    print("Error: %s" % str(err))
                    sys.exit(1)
                    
            except OSError as err:
                logger.debug("Error in message: %s" % str(ByteToHex(message)))
                logger.debug("Error: %s" % str(err))
                logger.debug("Traceback: " + traceback.format_exc())
                print("Error: Serial error (%s) " % str(ByteToHex(message)))
                break
            
    except KeyboardInterrupt:
        logger.debug("Received keyboard interrupt")
        pass
        
    logger.debug("Close serial port")
    try:
        s.device.close()
        logger.debug("Serial port closed")
    except:
        logger.debug("Error: Failed to close the serial port (%s)" % str(s.port))
        print("Error: Failed to close the port %s" % str(s.port))
        return False
    
    return result

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    
    r = rfxcmd_data()
    s = serial_data()
    
    parser = optparse.OptionParser()
    parser.add_option("-d", "--device", action="store", type="string", dest="device", help="Serial device of the RFXtrx433")
    parser.add_option("-l", "--list", action="store_true", dest="list", help="List all protocols")
    parser.add_option("-p", "--protocol", action="store", type="string", dest="protocol", help="Protocol number")
    parser.add_option("-s", "--setstate", action="store", type="string", dest="state", help="Set protocol state (on or off)")
    parser.add_option("-v", "--save", action="store_true", dest="save", help="Save current settings in device (Note device have limited write cycles)")
    parser.add_option("-V", "--version", action="store_true", dest="version", help="Print rfxcmd version information")
    parser.add_option("-D", "--debug", action="store_true", dest="debug", help="Debug logging on screen")
    
    (options, args) = parser.parse_args()
    
    if options.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.ERROR
    
    # Logging
    formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(module)s:%(lineno)d - %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger("RFXPROTO")
    logger.setLevel(loglevel)
    logger.addHandler(handler)
    
    logger.debug("Logger started")
    logger.debug("Version: %s" % __version__)
    logger.debug("Date: %s" % __date__.replace('$', ''))
    
    if options.version:
        logger.debug("Print version")
        print_version()
    
    if options.device:
        s.port=options.device
        logger.debug("Serial device: %s" % str(s.port))
    else:
        s.port=None
        logger.debug("Serial device: %s" % str(s.port))
    
    # Set protocol state
    if options.protocol:
        pnum = int(options.protocol)
        if options.state == "on" or options.state == "off":
            if not s.port == None:
                logger.debug("Protocol num: %s" % str(pnum))
                logger.debug("Protocol state: %s" % options.state)
                if options.state == "on":
                    rfx_setmode(pnum, 1)
                else:
                    rfx_setmode(pnum, 0)
            else:
                logger.debug("Error: Serial device is missing")
                print("Error: Serial device is missing")
        else:
            logger.debug("Error: Unknown state parameter for protocol")
            print("Error: Unknown state parameter for protocol")
            
    # Get current status
    if options.list:
        if not s.port == None:
            logger.debug("Get current state")
            try:
                result = rfx_sendmsg(r.status)
                logger.debug("Result: %s" % str(ByteToHex(result)))
                if result:
                    rfx_decodestatus(result)
                else:
                    print("Invalid result received")
            except Exception as err:
                logger.debug("Error: Send failed, error: %s" % str(err))
                print("Error: Could not send message: %s " % err)
        else:
            logger.debug("Error: Serial device is missing")
            print("Error: Serial device is missing")
        
    logger.debug("Exit")
    sys.exit(0)

# ------------------------------------------------------------------------------
# END
# ------------------------------------------------------------------------------
