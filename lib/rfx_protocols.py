#!/usr/bin/python
# coding=UTF-8

"""
    
    RFX_PROTOCOLS.PY
    
    Copyright (C) 2012-2013 Sebastian Sjoholm, sebastian.sjoholm@gmail.com
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
    Version history can be found at 
    http://code.google.com/p/rfxcmd/wiki/VersionHistory

    $Rev: 464 $
    $Date: 2013-05-01 22:41:36 +0200 (Wed, 01 May 2013) $

"""

# ------------------------------------------------------------------------------

import logging
logger = logging.getLogger('rfxcmd')

# ------------------------------------------------------------------------------

import sys
import xml.dom.minidom as minidom

# ------------------------------------------------------------------------------

def print_protocolfile(protocol_file):
    """
    Print the contents of the protocol configuration file to stdout
    """

    logger.debug("Open protocol file and read it, file: %s" % str(protocol_file))
    try:
        xmldoc = minidom.parse( protocol_file )
        logger.debug("XML file OK")
    except:
        print("Error in %s file" % str(protocol_file))
        sys.exit(1)

    try:
        data = xmldoc.documentElement.getElementsByTagName('protocol')
    except Exception as err:
        logger.error("Error: %s" % str(err))
        sys.exit(1)

    logger.debug("Read protocol tags in file")
    counter = 0

    print("Protocol.xml configuration")
    print("-----------------------------------")

    for protocol in data:
        try:
            id = int(protocol.getElementsByTagName('id')[0].childNodes[0].nodeValue)
        except Exception as err:
            logger.error("Error: %s" % str(err))
            sys.exit(1)

        if id != counter:
            print("Error: The id number is not in order")
            sys.exit(1)

        try:
            name = protocol.getElementsByTagName('name')[0].childNodes[0].nodeValue
        except Exception as err:
            logger.error("Error: %s" % str(err))
            sys.exit(1)

        try:
            state = int(protocol.getElementsByTagName('state')[0].childNodes[0].nodeValue)
            if state == 1:
                state_str = "Enabled"
            else:
                state_str = "Disabled"
        except Exception as err:
            logger.error("Error: %s" % str(err))
            sys.exit(1)

        if state != 0 and state != 1:
            print("Error: The state is either 0 or 1, in protocol '%s'" % str(name))
            sys.exit(1)

        print("%-25s %-15s" % (str(name), str(state_str)))
        logger.debug("Id: %s, State: %s, Counter: %s, Name: %s " % (str(id), str(state), str(counter), str(name)))
        counter += 1

    logger.debug("Tags total: %s" % str(counter))

    if counter != 24:
        logger.error("Error: There is not 24 protocol tags in protocol file")
        print("Error: There is not 24 protocol tags in protocol file")
        sys.exit(1)
    else:
        logger.debug("All tags found")

    return

# ------------------------------------------------------------------------------
def set_protocolfile(protocol_file):
    """
    Create the data message out of the protocol configuration file and return the packet
    """

    logger.debug("Open protocol file and read it, file: %s" % str(protocol_file))
    try:
        xmldoc = minidom.parse( protocol_file )
        logger.debug("XML file OK")
    except:
        print("Error in %s file" % str(protocol_file))
        sys.exit(1)

    try:
        data = xmldoc.documentElement.getElementsByTagName('protocol')
    except Exception as err:
        logger.error("Error: %s" % str(err))
        sys.exit(1)

    logger.debug("Read protocol tags in file")
    counter = 0

    msg = []
    msg3 = []
    msg4 = []
    msg5 = []

    for protocol in data:
        try:
            id = int(protocol.getElementsByTagName('id')[0].childNodes[0].nodeValue)
        except Exception as err:
            logger.error("Error: %s" % str(err))
            sys.exit(1)

        if id != counter:
            print("Error: The id number is not in order")
            sys.exit(1)

        try:
            name = protocol.getElementsByTagName('name')[0].childNodes[0].nodeValue
        except Exception as err:
            logger.error("Error: %s" % str(err))
            sys.exit(1)

        try:
            state = int(protocol.getElementsByTagName('state')[0].childNodes[0].nodeValue)
        except Exception as err:
            logger.error("Error: %s" % str(err))
            sys.exit(1)

        if state != 0 and state != 1:
            print("Error: The state is either 0 or 1, in protocol '%s'" % str(name))
            sys.exit(1)

        logger.debug("Id: %s, State: %s, Counter: %s, Name: %s " % (str(id), str(state), str(counter), str(name)))
        msg.insert(id, state)
        counter += 1

    logger.debug("Tags total: %s" % str(counter))

    if counter <> 24:
        logger.error("Error: There is not 24 protocol tags in protocol file")
        print("Error: There is not 24 protocol tags in protocol file")
        sys.exit(1)
    else:
        logger.debug("All tags found")

    msg3 = msg[0:8]
    msg4 = msg[8:16]
    msg5 = msg[16:24]

    # Complete message
    try:
        msg3_bin = str(msg[0]) + str(msg[1]) + str(msg[2]) + str(msg[3]) + str(msg[4]) + str(msg[5]) + str(msg[6]) + str(msg[7])
        msg3_int = int(msg3_bin,2)
        msg3_hex = hex(msg3_int)[2:].zfill(2)
        msg4_bin = str(msg[8]) + str(msg[9]) + str(msg[10]) + str(msg[11]) + str(msg[12]) + str(msg[13]) + str(msg[14]) + str(msg[15])
        msg4_int = int(msg4_bin,2)
        msg4_hex = hex(msg4_int)[2:].zfill(2)
        msg5_bin = str(msg[16]) + str(msg[17]) + str(msg[18]) + str(msg[19]) + str(msg[20]) + str(msg[21]) + str(msg[22]) + str(msg[23])
        msg5_int = int(msg5_bin,2)
        msg5_hex = hex(msg5_int)[2:].zfill(2)
    except Exception as err:
        logger.error("Error: %s" % str(err))
        sys.exit(1)

    logger.debug("msg3: %s / %s" % (str(msg3), msg3_hex))
    logger.debug("msg4: %s / %s" % (str(msg4), msg4_hex))
    logger.debug("msg5: %s / %s" % (str(msg5), msg5_hex))

    command = "0D000000035300%s%s%s00000000" % (msg3_hex, msg4_hex, msg5_hex)
    logger.debug("Command: %s" % command.upper())

    return command

# ------------------------------------------------------------------------------
# EOF
# ------------------------------------------------------------------------------
