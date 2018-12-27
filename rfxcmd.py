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
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
from string import whitespace
import sys
import os
import time
import binascii
import traceback
import re
import logging
import signal
import xml.dom.minidom as minidom
from optparse import OptionParser
import socket
import inspect

# Debug
# from pdb import set_trace as st

# RFXCMD modules
try:
    from lib.rfx_socket import *
except ImportError:
    logger.error("Error: importing module from lib folder")
    sys.exit(1)

try:
    from lib.rfx_command import *
except ImportError:
    logger.error("Error: module lib/rfx_command not found")
    sys.exit(1)

try:
    from lib.rfx_utils import *
except ImportError:
    logger.error("Error: module lib/rfx_utils not found")
    sys.exit(1)

try:
    import lib.rfx_sensors
    import lib.rfx_decode as rfxdecode
    import lib.rfx_rrd as rfxrrd
    import lib.rfx_xplcom as xpl
    import lib.rfx_protocols as protocol
except ImportError as err:
    logger.error(str(err))
    sys.exit(1)

# 3rd party modules
# These might not be needed, depended on usage

# SQLite
try:
    import sqlite3
except ImportError:
    pass

# MySQL
try:
    import MySQLdb
except ImportError:
    pass

# PgSQL
try:
    import psycopg2
except ImportError:
    pass

# Serial
try:
    import serial
except ImportError:
    pass

# ------------------------------------------------------------------------------
# VARIABLE CLASSS
# ------------------------------------------------------------------------------

class config_data:
    def __init__(
        self,
        serial_active = True,
        serial_device = None,
        serial_rate = 38400,
        serial_timeout = 9,
        mysql_active = False,
        mysql_server = '',
        mysql_database = '',
        mysql_username = "",
        mysql_password = "",
        trigger_active = False,
        trigger_onematch = False,
        trigger_file = "",
        trigger_timeout = 10,
        sqlite_active = False,
        sqlite_database = "",
        sqlite_table = "",
        pgsql_active = False,
        pgsql_server = '',
        pgsql_database = '',
        pgsql_port = '',
        pgsql_username = '',
        pgsql_password = '',
        pgsql_table = '',
        loglevel = "info",
        logfile = "rfxcmd.log",
        graphite_active = False,
        graphite_server = "",
        graphite_port = "",
        program_path = "",
        xpl_active = False,
        xpl_host = "",
        xpl_sourcename = "rfxcmd-",
        xpl_includehostname = True,
        socketserver = False,
        sockethost = "",
        socketport = "",
        whitelist_active = False,
        whitelist_file = "",
        daemon_active = False,
        daemon_pidfile = "rfxcmd.pid",
        process_rfxmsg = True,
        weewx_active = False,
        weewx_config = "weewx.xml",
        rrd_active = False,
        rrd_path = "",
        barometric = 0,
        log_msg = False,
        log_msgfile = "",
        protocol_startup = False,
        protocol_file = "protocol.xml"
        ):

        self.serial_active = serial_active
        self.serial_device = serial_device
        self.serial_rate = serial_rate
        self.serial_timeout = serial_timeout
        self.mysql_active = mysql_active
        self.mysql_server = mysql_server
        self.mysql_database = mysql_database
        self.mysql_username = mysql_username
        self.mysql_password = mysql_password
        self.pgsql_active = pgsql_active
        self.pgsql_server = pgsql_server
        self.pgsql_database = pgsql_database
        self.pgsql_port = pgsql_port
        self.pgsql_username = pgsql_username
        self.pgsql_password = pgsql_password
        self.pgsql_table = pgsql_table
        self.trigger_active = trigger_active
        self.trigger_onematch = trigger_onematch
        self.trigger_file = trigger_file
        self.trigger_timeout = trigger_timeout
        self.sqlite_active = sqlite_active
        self.sqlite_database = sqlite_database
        self.sqlite_table = sqlite_table
        self.loglevel = loglevel
        self.logfile = logfile
        self.graphite_active = graphite_active
        self.graphite_server = graphite_server
        self.graphite_port = graphite_port
        self.program_path = program_path
        self.xpl_active = xpl_active
        self.xpl_host = xpl_host
        self.xpl_sourcename = xpl_sourcename
        self.xpl_includehostname = xpl_includehostname
        self.socketserver = socketserver
        self.sockethost = sockethost
        self.socketport = socketport
        self.whitelist_active = whitelist_active
        self.whitelist_file = whitelist_file
        self.daemon_active = daemon_active
        self.daemon_pidfile = daemon_pidfile
        self.process_rfxmsg = process_rfxmsg
        self.weewx_active = weewx_active
        self.weewx_config = weewx_config
        self.rrd_active = rrd_active
        self.rrd_path = rrd_path
        self.barometric = barometric
        self.log_msg = log_msg
        self.log_msgfile = log_msgfile
        self.protocol_startup = protocol_startup
        self.protocol_file = protocol_file

class cmdarg_data:
    def __init__(
        self,
        configfile = "",
        action = "",
        rawcmd = "",
        device = "",
        createpid = False,
        pidfile = "",
        printout_complete = True,
        printout_csv = False
        ):

        self.configfile = configfile
        self.action = action
        self.rawcmd = rawcmd
        self.device = device
        self.createpid = createpid
        self.pidfile = pidfile
        self.printout_complete = printout_complete
        self.printout_csv = printout_csv

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
        port = None,
        rate = 38400,
        timeout = 9
        ):

        self.port = port
        self.rate = rate
        self.timeout = timeout

# Store the trigger data from xml file
class trigger_data:
    def __init__(
        self,
        data = ""
        ):

        self.data = data

# Store the whitelist data from xml file
class whitelist_data:
    def __init__(
        self,
        data = ""
        ):

        self.data = data

# Store the sensor id that should be received by WeeWx
class weewx_data:
    def __init__(
        self,
        data = ""
        ):

        self.data = data

# ----------------------------------------------------------------------------
# DEAMONIZE
# Credit: George Henze
# ----------------------------------------------------------------------------

def shutdown():
    # clean up PID file after us
    logger.debug("Shutdown")

    if cmdarg.createpid:
        logger.debug("Removing PID file " + str(cmdarg.pidfile))
        os.remove(cmdarg.pidfile)

    if serial_param.port is not None:
        logger.debug("Close serial port")
        serial_param.port.close()
        serial_param.port = None

    logger.debug("Exit 0")
    sys.stdout.flush()
    os._exit(0)
    
def handler(signum=None, frame=None):
    if type(signum) != type(None):
        logger.debug("Signal %i caught, exiting..." % int(signum))
        shutdown()

def daemonize():

    try:
        pid = os.fork()
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("1st fork failed: %s [%d]" % (e.strerror, e.errno))

    os.setsid() 

    prev = os.umask(0)
    os.umask(prev and int('077', 8))

    try:
        pid = os.fork() 
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("2nd fork failed: %s [%d]" % (e.strerror, e.errno))

    dev_null = file('/dev/null', 'r')
    os.dup2(dev_null.fileno(), sys.stdin.fileno())

    if cmdarg.createpid == True:
        pid = str(os.getpid())
        logger.debug("Writing PID " + pid + " to " + str(cmdarg.pidfile))
        file(cmdarg.pidfile, 'w').write("%s\n" % pid)

# ----------------------------------------------------------------------------
# C __LINE__ equivalent in Python by Elf Sternberg
# http://www.elfsternberg.com/2008/09/23/c-__line__-equivalent-in-python/
# ----------------------------------------------------------------------------

def _line():
    info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
    return '[%s:%d]' % (info[2], info[1])

# ----------------------------------------------------------------------------

def send_graphite(CARBON_SERVER, CARBON_PORT, lines):
    """
    Send data to graphite
    Credit: Frédéric Pégé
    """ 
    sock = None
    for res in socket.getaddrinfo(CARBON_SERVER,int(CARBON_PORT), socket.AF_UNSPEC, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        try:
            sock = socket.socket(af, socktype, proto)
        except socket.error as msg:
            sock = None
            continue
        try:
            sock.connect(sa)
        except socket.error as msg:
            sock.close()
            sock = None
            continue
        break

    if sock is None:
        logger.error('could not open socket')
        sys.exit(1)
    
    message = '\n'.join(lines) + '\n' #all lines must end in a newline
    sock.sendall(message)
    sock.close()

# ----------------------------------------------------------------------------

def readbytes(number):
    """
    Read x amount of bytes from serial port. 
    Credit: Boris Smus http://smus.com
    """
    buf = ''
    for i in range(number):
        try:
            byte = serial_param.port.read()
        except IOError, e:
            logger.error(e)
        except OSError, e:
            logger.error(e)
        buf += byte

    return buf

# ----------------------------------------------------------------------------

def insert_database(timestamp, unixtime, packettype, subtype, seqnbr, battery, signal, data1, data2, data3,
        data4, data5, data6, data7, data8, data9, data10, data11, data12, data13):
    """
    Choose in which database insert datas
    """
    
    logger.debug('insert_database')
    
    # MYSQL
    if config.mysql_active:
        logger.debug('-> MySQL')
        insert_mysql(timestamp, unixtime, packettype, subtype, seqnbr, battery, signal, data1, data2, data3,
        data4, data5, data6, data7, data8, data9, data10, data11, data12, data13)

    # SQLITE
    if config.sqlite_active:
        logger.debug('-> SqLite')
        insert_sqlite(timestamp, unixtime, packettype, subtype, seqnbr, battery, signal, data1, data2, data3,
        data4, data5, data6, data7, data8, data9, data10, data11, data12, data13)

    # PGSQL
    if config.pgsql_active:
        logger.debug('-> PGSql')
        insert_pgsql(timestamp, unixtime, packettype, subtype, seqnbr, battery, signal, data1, data2, data3,
        data4, data5, data6, data7, data8, data9, data10, data11, data12, data13)

# ----------------------------------------------------------------------------

def insert_mysql(timestamp, unixtime, packettype, subtype, seqnbr, battery, signal, data1, data2, data3, 
    data4, data5, data6, data7, data8, data9, data10, data11, data12, data13):
    """
    Insert data to MySQL.
    """

    db = None

    try:

        if data13 == 0:
            data13 = "0000-00-00 00:00:00"

        db = MySQLdb.connect(config.mysql_server, config.mysql_username, config.mysql_password, config.mysql_database)
        cursor = db.cursor()
        sql = """
            INSERT INTO rfxcmd (datetime, unixtime, packettype, subtype, seqnbr, battery, rssi, processed, data1, data2, data3, data4,
                data5, data6, data7, data8, data9, data10, data11, data12, data13)
            VALUES ('%s','%s','%s','%s','%s','%s','%s',0,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')
            """ % (timestamp, unixtime, packettype, subtype, seqnbr, battery, signal, data1, data2, data3, data4, data5, data6, data7, 
                data8, data9, data10, data11, data12, data13)
        
        cursor.execute(sql)
        db.commit()

    except MySQLdb.Error, e:
        logger.error("Line: " + _line())
        logger.error("MySQL error %d: %s" % (e.args[0], e.args[1]))
        sys.exit(1)

    finally:
        if db:
            db.close()

# ----------------------------------------------------------------------------

def insert_sqlite(timestamp, unixtime, packettype, subtype, seqnbr, battery, signal, data1, data2, data3, 
    data4, data5, data6, data7, data8, data9, data10, data11, data12, data13):
    """
    Insert data to SqLite.
    """

    cx = None

    try:

        cx = sqlite3.connect(config.sqlite_database)
        cu = cx.cursor()
        sql = """
            INSERT INTO '%s' (datetime, unixtime, packettype, subtype, seqnbr, battery, rssi, processed, data1, data2, data3, data4,
                data5, data6, data7, data8, data9, data10, data11, data12, data13)
            VALUES('%s','%s','%s','%s','%s','%s','%s',0,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')
            """ % (config.sqlite_table, timestamp, unixtime, packettype, subtype, seqnbr, battery, signal, data1, data2, data3, 
                data4, data5, data6, data7, data8, data9, data10, data11, data12, data13)

        cu.executescript(sql)
        cx.commit()
                
    except sqlite3.Error, e:

        if cx:
            cx.rollback()
            
        logger.error("Line: " + _line())
        logger.error("SqLite error: %s" % e.args[0])
        sys.exit(1)
            
    finally:
        if cx:
            cx.close()

# ----------------------------------------------------------------------------

def insert_pgsql(timestamp, unixtime, packettype, subtype, seqnbr, battery, signal, data1, data2, data3,
        data4, data5, data6, data7, data8, data9, data10, data11, data12, data13):
    """
    Insert data to PgSQL
    Credits: Pierre-Yves
    """

    db = None

    dsn = "dbname='%s' user='%s' host='%s' port=%s password=%s" \
            % (config.pgsql_database, config.pgsql_username, config.pgsql_server, config.pgsql_port, config.pgsql_password)
    
    try:
        if data13 == 0:
            data13 = "NULL"
        
        db = psycopg2.connect(dsn)
        cursor = db.cursor()
        
        sql = """
                INSERT INTO %s (datetime, unixtime, packettype, subtype, seqnbr, battery, rssi, processed, data1, data2, data3, data4,
                data5, data6, data7, data8, data9, data10, data11, data12, data13)
                VALUES ('%s','%s','%s','%s','%s','%s','%s',0,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s', '%s UTC')
                """ % (config.pgsql_table, timestamp, unixtime, packettype, subtype, seqnbr, battery, signal, data1, data2, data3, data4, data5, data6, data7,
                data8, data9, data10, data11, data12, data13)
        
        logger.debug("SQL: %s" % str(sql))
        
        cursor.execute(sql)
        db.commit()
        
    except psycopg2.DatabaseError, e:
        logger.error("Line: " + _line())
        logger.error("Error : (PgSQL Query) : %s " % e)
        sys.exit(1)
    
    finally:
        if db:
            db.close() 

# ----------------------------------------------------------------------------

def decodePacket(message):
    """
    Decode incoming RFXtrx message.
    """
    
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    unixtime_utc = int(time.time())

    decoded = False
    db = ""
    
    # Verify incoming message
    logger.debug("Verify incoming packet")
    if not test_rfx( ByteToHex(message) ):
        logger.error("The incoming message is invalid (" + ByteToHex(message) + ") Line: " + _line())
        if cmdarg.printout_complete == True:
            logger.error("Error: The incoming message is invalid " + _line())
            return
    else:
        logger.debug("Verified OK")
    
    raw_message = ByteToHex(message)
    raw_message = raw_message.replace(' ', '')
    
    packettype = ByteToHex(message[1])
    logger.debug("PacketType: %s" % str(packettype))
    
    if len(message) > 2:
        subtype = ByteToHex(message[2])
        logger.debug("SubType: %s" % str(subtype))
    
    if len(message) > 3:
        seqnbr = ByteToHex(message[3])
        logger.debug("SeqNbr: %s" % str(seqnbr))
        
    if len(message) > 4:
        id1 = ByteToHex(message[4])
        logger.debug("Id1: %s" % str(id1))
        
    if len(message) > 5:
        id2 = ByteToHex(message[5])
        logger.debug("Id2: %s" % str(id2))
    
    if cmdarg.printout_complete:
        logger.info("Packettype\t\t= " + rfx.rfx_packettype[packettype])
    
    # ---------------------------------------
    # Check if the packet is a special WeeWx packet
    # 0A1100FF001100FF001100
    # ---------------------------------------
    if raw_message == "0A1100FF001100FF001100":
        logger.debug("Incoming WeeWx packet, do not decode")
        if cmdarg.printout_complete:
            logger.info("Info\t\t\t= Incoming WeeWx packet")
        decoded = True
        return
        
    # ---------------------------------------
    # Verify correct length on packets
    # ---------------------------------------
    logger.debug("Verify correct packet length")
    if packettype == '00' and len(message) != 14:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None

    if packettype == '01' and len(message) != 14 and len(message) != 21:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '02' and len(message) != 5:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '10' and len(message) != 8:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '11' and len(message) != 12:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '12' and len(message) != 9:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '13' and len(message) != 10:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '15' and len(message) != 12:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '16' and len(message) != 8:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '17' and len(message) != 8:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '18' and len(message) != 8:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '19' and len(message) != 10:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '1A' and len(message) != 13:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '20' and len(message) != 9:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '28' and len(message) != 7:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '30' and len(message) != 7:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '40' and len(message) != 10:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '41' and len(message) != 7:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '42' and len(message) != 9:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '4E' and len(message) != 11:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '4F' and len(message) != 11:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '50' and len(message) != 9:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '51' and len(message) != 9:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '52' and len(message) != 11:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '53' and len(message) != 10:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '54' and len(message) != 14:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '55' and len(message) != 12:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '56' and len(message) != 17:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '57' and len(message) != 10:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '58' and len(message) != 14:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '59' and len(message) != 14:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '5A' and len(message) != 18:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '5B' and len(message) != 20:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '5C' and len(message) != 16:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '5D' and len(message) != 9:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '70' and len(message) != 8:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '71' and len(message) != 11:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    if packettype == '72' and len(message) != 10:
        logger.error("Packet has wrong length, discarding")
        decoded = True
        packettype = None
    
    # ---------------------------------------
    # If packet is OK and the log_msg is active
    # then save the packet to log_msgfile designated
    # file on disk
    # ---------------------------------------
    if decoded == False and config.log_msg == True:
        logger.debug("Save packet to log_msgfile")
        try:
            data = str(ByteToHex(message))
            data = data.replace(' ', '')
            file = open(config.log_msgfile,"a+")
            file.write(data + "\n")
            file.close()
        except Exception, e:
            logger.error("Error when trying to write message log")
            logger.error("Exception: %s" % str(e))
            pass
        
    # ---------------------------------------
    # 0x0 - Interface Control
    # ---------------------------------------
    if packettype == '00':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
    
    # ---------------------------------------
    # 0x01 - Interface Message
    # ---------------------------------------
    if packettype == '01':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        if cmdarg.printout_complete:
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
                logger.info("Subtype\t\t\t= Interface response")
            else:
                logger.info("Subtype\t\t\t= Unknown type (" + data['packettype'] + ")")
            
            # Seq
            logger.info("Sequence nbr\t\t= " + data['seqnbr'])
            
            # Command
            logger.info("Response on cmnd\t= " + rfx.rfx_cmnd[data['cmnd']])
            
            # MSG 1
            logger.info("Transceiver type\t= " + rfx.rfx_subtype_01_msg1[data['msg1']])
            
            # MSG 2
            logger.info("Firmware version\t= " + str(int(data['msg2'],16)))
            
            logger.info("Protocols:")
            
            # ------------------------------------------------------
            # MSG 3
            
            protocol = str(rfx.rfx_subtype_01_msg3['128'])
            if testBit(int(data['msg3'],16),7) == 128:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg3['64'])
            if testBit(int(data['msg3'],16),6) == 64:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg3['32'])
            if testBit(int(data['msg3'],16),5) == 32:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg3['16'])
            if testBit(int(data['msg3'],16),4) == 16:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg3['8'])
            if testBit(int(data['msg3'],16),3) == 8:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg3['4'])
            if testBit(int(data['msg3'],16),2) == 4:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg3['2'])
            if testBit(int(data['msg3'],16),1) == 2:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg3['1'])
            if testBit(int(data['msg3'],16),0) == 1:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            # ------------------------------------------------------
            # MSG 4
            
            protocol = str(rfx.rfx_subtype_01_msg4['128'])
            if testBit(int(data['msg4'],16),7) == 128:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg4['64'])
            if testBit(int(data['msg4'],16),6) == 64:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg4['32'])
            if testBit(int(data['msg4'],16),5) == 32:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg4['16'])
            if testBit(int(data['msg4'],16),4) == 16:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg4['8'])
            if testBit(int(data['msg4'],16),3) == 8:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg4['4'])
            if testBit(int(data['msg4'],16),2) == 4:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg4['2'])
            if testBit(int(data['msg4'],16),1) == 2:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg4['1'])
            if testBit(int(data['msg4'],16),0) == 1:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            # ------------------------------------------------------
            # MSG 5
            
            protocol = str(rfx.rfx_subtype_01_msg5['128'])
            if testBit(int(data['msg5'],16),7) == 128:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg5['64'])
            if testBit(int(data['msg5'],16),6) == 64:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg5['32'])
            if testBit(int(data['msg5'],16),5) == 32:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg5['16'])
            if testBit(int(data['msg5'],16),4) == 16:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg5['8'])
            if testBit(int(data['msg5'],16),3) == 8:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg5['4'])
            if testBit(int(data['msg5'],16),2) == 4:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg5['2'])
            if testBit(int(data['msg5'],16),1) == 2:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
            protocol = str(rfx.rfx_subtype_01_msg5['1'])
            if testBit(int(data['msg5'],16),0) == 1:
                logger.info("%-25s Enabled" % protocol)
            else:
                logger.info("%-25s Disabled" % protocol)
            
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x02 - Receiver/Transmitter Message
    # ---------------------------------------
    if packettype == '02':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        
        decoded = True
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_02[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)

            if subtype == '01':
                logger.info("Message\t\t\t= " + rfx.rfx_subtype_02_msg1[id1])
        
        # CSV
        if cmdarg.printout_csv == True:
            if subtype == '00':
                sys.stdout.write("%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr ) )
            else:
                sys.stdout.write("%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, id1 ) )
            sys.stdout.flush()
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            if subtype == '00':
                insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            else:
                insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, 255, str(id1), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x03 - Undecoded Message
    # ---------------------------------------
    if packettype == '03':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        indata = ByteToHex(message)
        
        # remove all spaces
        for x in whitespace:
            indata = indata.replace(x,"")
        
        indata = indata[4:]
        
        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_03[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Message\t\t\t= " + indata)
        
        # CSV
        if cmdarg.printout_csv:
            sys.stdout.write("%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, indata ))
            sys.stdout.flush()
            
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$message$", indata )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, 255, indata, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x10 Lighting1
    # ---------------------------------------
    if packettype == '10':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")

        decoded = True
        
        # DATA
        try:
            housecode = rfx.rfx_subtype_10_housecode[ByteToHex(message[4])]
        except Exception as err:
            housecode = "Error: Unknown housecode"
            logger.error("Unknown house command received, %s" % str(err))
            pass
            
        unitcode = int(ByteToHex(message[5]), 16)
        try:
            command = rfx.rfx_subtype_10_cmnd[ByteToHex(message[6])]
        except Exception as err:
            command = "Error: Unknown command"
            logger.error("Unknown command received, %s" % str(err))
            pass
        
        signal = rfxdecode.decodeSignal(message[7])
        
        try:
            subtype_str = str(rfx.rfx_subtype_10[subtype])
        except Exception as err:
            subtype = "Error: Unknown subtype"
            logger.error("Unknown subtype received, %s" % str(err))
            pass
        
        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= %s" % subtype_str)
            logger.info("Seqnbr\t\t\t= %s" % str(seqnbr))
            logger.info("Housecode\t\t= %s" % str(housecode))
            logger.info("Unitcode\t\t= %s" % str(unitcode))
            logger.info("Command\t\t\t= %s" % str(command))
            logger.info("Signal level\t\t= %s" % str(signal))

        # CSV
        if cmdarg.printout_csv:
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), housecode, command, str(unitcode) ))
            sys.stdout.flush()
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$housecode$", str(housecode) )
                    action = action.replace("$unitcode$", str(unitcode) )
                    action = action.replace("$command$", command )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, housecode, 0, command, unitcode, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Lightning.'+housecode+str(unitcode)+'\ntype=command\ncurrent='+command+'\n', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Lightning.'+housecode+str(unitcode)+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x11 Lighting2
    # ---------------------------------------
    if packettype == '11':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = ByteToHex(message[4]) + ByteToHex(message[5]) + ByteToHex(message[6]) + ByteToHex(message[7])
        unitcode = int(ByteToHex(message[8]),16)
        command = rfx.rfx_subtype_11_cmnd[ByteToHex(message[9])]
        dimlevel = rfx.rfx_subtype_11_dimlevel[ByteToHex(message[10])]
        signal = rfxdecode.decodeSignal(message[11])

        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_11[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + sensor_id)
            logger.info("Unitcode\t\t= " + str(unitcode))
            logger.info("Command\t\t\t= " + command)
            logger.info("Dim level\t\t= " + dimlevel + "%")
            logger.info("Signal level\t\t= " + str(signal))
        
        # CSV
        if cmdarg.printout_csv:
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), sensor_id, command, str(unitcode), dimlevel ))
            sys.stdout.flush()

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$unitcode$", str(unitcode) )
                    action = action.replace("$command$", command )
                    action = action.replace("$dimlevel$", dimlevel )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, 0, command, unitcode, int(dimlevel), 0, 0, 0, 0, 0, 0, 0, 0)

        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Lightning.'+sensor_id+'\ntype=command\ncurrent='+command+'\n', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Lightning.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x12 Lighting3
    # ---------------------------------------
    if packettype == '12':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        system = ByteToHex(message[4])
        
        if testBit(int(ByteToHex(message[5]),16),0) == 1:
            channel = 1
        elif testBit(int(ByteToHex(message[5]),16),1) == 2:
            channel = 2
        elif testBit(int(ByteToHex(message[5]),16),2) == 4:
            channel = 3
        elif testBit(int(ByteToHex(message[5]),16),3) == 8:
            channel = 4
        elif testBit(int(ByteToHex(message[5]),16),4) == 16:
            channel = 5
        elif testBit(int(ByteToHex(message[5]),16),5) == 32:
            channel = 6
        elif testBit(int(ByteToHex(message[5]),16),6) == 64:
            channel = 7
        elif testBit(int(ByteToHex(message[5]),16),7) == 128:
            channel = 8
        elif testBit(int(ByteToHex(message[6]),16),0) == 1:
            channel = 9
        elif testBit(int(ByteToHex(message[6]),16),1) == 2:
            channel = 10
        else:
            channel = 255

        command = rfx.rfx_subtype_12_cmnd[ByteToHex(message[7])]
        battery = rfxdecode.decodeBattery(message[8])
        signal = rfxdecode.decodeSignal(message[8])

        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_12[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("System\t\t\t= " + system)
            logger.info("Channel\t\t\t= " + str(channel))
            logger.info("Command\t\t\t= " + command)
            logger.info("Battery\t\t\t= " + str(battery))
            logger.info("Signal level\t\t= " + str(signal))

        # CSV 
        if cmdarg.printout_csv:
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;\n" %(timestamp, packettype, subtype, seqnbr, str(battery), str(signal), str(system), command, str(channel) ))
            sys.stdout.flush()

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$system$", str(system) )
                    action = action.replace("$channel$", str(channel) )
                    action = action.replace("$command$", command )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, str(system), 0, command, str(channel), 0, 0, 0, 0, 0, 0, 0, 0, 0)

        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Lightning.'+str(channel)+'\ntype=command\ncurrent='+command+'\n', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Lightning.'+str(channel)+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x13 Lighting4
    # ---------------------------------------
    if packettype == '13':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        code = ByteToHex(message[4]) + ByteToHex(message[5]) + ByteToHex(message[6])
        code1 = dec2bin(int(ByteToHex(message[4]),16))
        code2 = dec2bin(int(ByteToHex(message[5]),16))
        code3 = dec2bin(int(ByteToHex(message[6]),16))
        code_bin = code1 + " " + code2 + " " + code3
        pulse = ((int(ByteToHex(message[7]),16) * 256) + int(ByteToHex(message[8]),16))
        signal = rfxdecode.decodeSignal(message[9])     
        
        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_13[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Code\t\t\t= " + code)
            logger.info("S1-S24\t\t\t= "  + code_bin)
            logger.info("Pulse\t\t\t= " + str(pulse) + " usec")
            logger.info("Signal level\t\t= " + str(signal))

        # CSV
        if cmdarg.printout_csv:
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, code, code_bin, str(pulse), str(signal) ))
            sys.stdout.flush()

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$code$", code_bin )
                    action = action.replace("$pulse$", str(pulse) )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 0, signal, 0, 0, str(code_bin), pulse, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x14 Lighting5
    # ---------------------------------------
    if packettype == '14':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2 + ByteToHex(message[6])
        unitcode = int(ByteToHex(message[7]),16)
        
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
                logger.error("Value is not in the sensor list")
                command = "Select Color"
                pass
        else:
            command = "Unknown"
        
        if subtype == "00":
            level = ByteToHex(message[9])
        else:
            level = 0
        
        signal = rfxdecode.decodeSignal(message[10])
        
        try:
            subtype_str = rfx.rfx_subtype_14[subtype]
        except Exception as err:
            logger.error("Error: Invalid subtype")
            subtype_str = "Unknown"
            pass
            
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= %s" % subtype_str)
            logger.info("Seqnbr\t\t\t= %s" % str(seqnbr))
            logger.info("Id\t\t\t= %s" % str(sensor_id))
            
            if subtype != '03' and subtype != '05':
                logger.info("Unitcode\t\t= Not used")
                unitcode = 0
            else:
                logger.info("Unitcode\t\t= " + str(unitcode))
            
            logger.info("Command\t\t\t= " + command)
            
            if subtype == '00':
                logger.info("Level\t\t\t= " + level)
            
            logger.info("Signal level\t\t= " + str(signal))
    
        # CSV
        if cmdarg.printout_csv:
            if subtype == '00':
                sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, sensor_id, str(unitcode), command, level, str(signal) ))
            else:
                sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, sensor_id, str(unitcode), command, str(signal) ))
            sys.stdout.flush()

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$unitcode$", str(unitcode) )
                    action = action.replace("$command$", command )
                    if subtype == '00':         
                        action = action.replace("$level$", level )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return

        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 0, signal, sensor_id, 0, command, str(unitcode), level, 0, 0, 0, 0, 0, 0, 0, 0)
        
        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Lightning.'+sensor_id+'\ntype=command\ncurrent='+command+'\n', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Lightning.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x15 Lighting6
    # Credit: Dimitri Clatot
    # ---------------------------------------
    if packettype == '15':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        groupcode = rfx.rfx_subtype_15_groupcode[ByteToHex(message[6])]
        unitcode = int(ByteToHex(message[7]),16)
        command = rfx.rfx_subtype_15_cmnd[ByteToHex(message[8])]
        command_seqnbr = ByteToHex(message[9])
        seqnbr2 = ByteToHex(message[10])
        signal = rfxdecode.decodeSignal(message[11])

        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_15[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("ID\t\t\t= "  + sensor_id)
            logger.info("Groupcode\t\t= " + groupcode)
            logger.info("Unitcode\t\t= " + str(unitcode))
            logger.info("Command\t\t\t= " + command)
            logger.info("Command seqnbr\t\t= " + command_seqnbr)
            logger.info("Seqnbr2\t\t\t= %s" % str(seqnbr2))
            logger.info("Signal level\t\t= " + str(signal))

        # CSV
        if cmdarg.printout_csv:
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, sensor_id, str(signal), groupcode, command, str(unitcode), str(command_seqnbr) ))
            sys.stdout.flush()
            
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$groupcode$", groupcode )
                    action = action.replace("$unitcode$", str(unitcode) )
                    action = action.replace("$command$", command )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return

        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, groupcode, command, unitcode, command_seqnbr, 0, 0, 0, 0, 0, 0, 0, 0)

        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Lightning.'+sensor_id+'\ntype=command\ncurrent='+command+'\n', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Lightning.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
    
    # --------------------------------------------------------------------------
    # 0x16 Chime
    # --------------------------------------------------------------------------
    if packettype == "16":
        logger.debug("Decode packetType 0x%s - Start", str(packettype))
        decoded = True

        # DATA
        sensor_id = id1 + id2

        if subtype == "00":
            try:
                sound = rfx.rfx_subtype_16_sound[ByteToHex(message[6])]
            except Exception as err:
                logger.error(err)
                sound = "Unknown"

        elif subtype == "01":
            sound = str(ByteToHex(message[6]))

        elif subtype == "02" or subtype == "03" or subtype == "04":
            sound = None

        try:
            signal = rfxdecode.decodeSignal(message[7])
        except Exception as err:
            logger.error(err)
            signal = "Error"
        
        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= %s" % str(rfx.rfx_subtype_16[subtype]))
            logger.info("Seqnbr\t\t\t= %s" % str(seqnbr))
            logger.info("ID\t\t\t= %s" % str(sensor_id))
            if sound != None:
                logger.info("Sound\t\t\t= %s" % str(sound))
            logger.info("Signal level\t\t= %s" % str(signal))
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: %s, Action: %s", str(trigger_message), str(action))
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    if sound != None:
                        action = action.replace("$sound$", sound )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            logger.error("Database not supported yet for this sensor 0x16")
            #insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        logger.debug("Decode packetType 0x%s - End", str(packettype))
        
    
    # ---------------------------------------
    # 0x17 Fan (Transmitter only)
    # ---------------------------------------
    if packettype == '17':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_18[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("This sensor is not completed, please send printout to sebastian.sjoholm@gmail.com")

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        #if config.mysql_active or config.sqlite_active or config.pgsql_active:
        #   insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
    
    # ---------------------------------------
    # 0x18 Curtain1 (Transmitter only)
    # ---------------------------------------
    if packettype == '18':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # PRINTOUT      
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_18[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("This sensor is not completed, please send printout to sebastian.sjoholm@gmail.com")

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return

        # DATABASE
        #if config.mysql_active or config.sqlite_active or config.pgsql_active:
        #   insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x19 Blinds1
    # ---------------------------------------
    if packettype == '19':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")

        decoded = True
        
        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_19[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("This sensor is not completed, please send printout to sebastian.sjoholm@gmail.com")

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return

        # DATABASE
        #if config.mysql_active or config.sqlite_active or config.pgsql_active:
        #   insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
    
    # ---------------------------------------
    # 0x1A RTS
    # ---------------------------------------
    if packettype == '1A':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2 + ByteToHex(message[6])
        
        try:
            subtype_str = rfx.rfx_subtype_1A[subtype]
        except Exception as err:
            logger.error("Unknown subtype")
            subtype = "Error: Unknown subtype"
            pass
        
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
            logger.error("Unknown command received")
            command_str = "Error: Unknown command received"
            pass
        
        signal = rfxdecode.decodeSignal(message[8])
        
        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= %s" % str(subtype_str))
            logger.info("Seqnbr\t\t\t= %s" % str(seqnbr))
            logger.info("Id1-3\t\t\t= %s" % str(sensor_id))
            logger.info("Unitcode\t\t= %s" % unitcode_str)
            logger.info("Command\t\t\t= %s" % command_str)
            logger.info("Signal level\t\t= " + str(signal))
        
        # CSV
        if cmdarg.printout_csv:
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(battery), str(signal), sensor_id, unitcode_str, command_str ) )
            sys.stdout.flush()
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", str(subtype) )
                    action = action.replace("$unitcode$", str(unitcode) )
                    action = action.replace("$command$", str(command) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        #if config.mysql_active or config.sqlite_active or config.pgsql_active:
        #   insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
    
    # ---------------------------------------
    # 0x20 Security1
    # Credit: Dimitri Clatot
    # ---------------------------------------
    if packettype == '20':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True

        # DATA
        sensor_id = id1 + id2 + ByteToHex(message[6])
        status = rfx.rfx_subtype_20_status[ByteToHex(message[7])]
        signal = rfxdecode.decodeSignal(message[8])
        battery = rfxdecode.decodeBattery(message[8])
        try:
            display_subtype = rfx.rfx_subtype_20[subtype]
        except KeyError:
            display_subtype = 'Unknown'

        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= " + display_subtype)
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t\t= " + sensor_id)
            logger.info("Status\t\t\t= " + status)
            logger.info("Battery\t\t\t= " + str(battery))
            logger.info("Signal level\t\t= " + str(signal))

        # CSV
        if cmdarg.printout_csv:
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(battery), str(signal), sensor_id, status ) )
            sys.stdout.flush()

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$status$", status )
                    action = action.replace("$battery$", str(battery) )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
            
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, status, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x28 Camera1
    # ---------------------------------------
    if packettype == '28':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
    
        decoded = True
        
        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_28[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("This sensor is not completed, please send printout to sebastian.sjoholm@gmail.com")
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return

        # DATABASE
        #if config.mysql_active or config.sqlite_active or config.pgsql_active:
        #   insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x30 Remote control and IR
    # ---------------------------------------
    if packettype == '30':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
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
            signal = rfxdecode.decodeSignal(message[6])
        
        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_30[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + id1)
            logger.info("Command\t\t\t= " + command)
            if subtype == '04':
                logger.info("Toggle\t\t\t= " + toggle)
            if subtype == '04':
                logger.info("CommandType\t= " + cmndtype)
            logger.info("Signal level\t\t= " + str(signal))
        
        # CSV 
        if cmdarg.printout_csv:
            logger.debug("CSV Output")
            if subtype == '00' or subtype == '02':
                sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), id1, command))
            elif subtype == '04' or subtype == '01' or subtype == '03':
                command = "Not implemented in RFXCMD"
            sys.stdout.flush()

        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", id1 )
                    action = action.replace("$command$", command )
                    if subtype == '04':
                        action = action.replace("$toggle$", toggle )
                        action = action.replace("$command$", cmndtype )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            if subtype == '00' or subtype == '02':
                insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 0, signal, id1, 0, command, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            elif subtype == '04' or subtype == '01' or subtype == '03':
                command = "Not implemented in RFXCMD"
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x40 - Thermostat1
    # Credit: Jean-François Pucheu
    # ---------------------------------------
    if packettype == '40':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        temperature = int(ByteToHex(message[6]), 16)
        temperature_set = int(ByteToHex(message[7]), 16)
        status_temp = str(testBit(int(ByteToHex(message[8]),16),0) + testBit(int(ByteToHex(message[8]),16),1))
        status = rfx.rfx_subtype_40_status[status_temp]
        if testBit(int(ByteToHex(message[8]),16),7) == 128:
            mode = rfx.rfx_subtype_40_mode['1']
        else:
            mode = rfx.rfx_subtype_40_mode['0']
        signal = rfxdecode.decodeSignal(message[9])

        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_40[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + sensor_id)
            logger.info("Temperature\t\t= " + str(temperature) + " C")
            logger.info("Temperature set\t\t= " + str(temperature_set) + " C")
            logger.info("Mode\t\t\t= " + mode)
            logger.info("Status\t\t\t= " + status)
            logger.info("Signal level\t\t= " + str(signal))

        # CSV 
        if cmdarg.printout_csv:
            logger.debug("CSV Output")
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), mode, status, str(temperature_set), str(temperature) ))
            sys.stdout.flush()
    
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$temperature$", str(temperature) )
                    action = action.replace("$temperatureset$", str(temperature_set) )
                    action = action.replace("$mode$", mode )
                    action = action.replace("$status$", status )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, sensor_id, mode, status, 0, 0, 0, temperature_set, temperature, 0, 0, 0, 0, 0)

        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Thermostat.'+sensor_id+'\ntype=temperature\ncurrent='+temperature+'\nunits=C', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Thermostat.'+sensor_id+'\ntype=temperature_set\ncurrent='+temperature_set+'\nunits=C', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Thermostat.'+sensor_id+'\ntype=mode\ncurrent='+mode+'\n', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Thermostat.'+sensor_id+'\ntype=status\ncurrent='+mode+'\n', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Thermostat.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Thermostat.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x41 Thermostat2
    # ---------------------------------------
    if packettype == '41':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_41[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            # TODO
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x42 Thermostat3
    # ---------------------------------------
    if packettype == '42':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        if subtype == '00':
            unitcode = ByteToHex(message[4])
        elif subtype == '01':
            unitcode = ByteToHex(message[4]) + ByteToHex(message[5]) + ByteToHex(message[6])
        else:
            unitcode = "00"
        
        logger.debug("Unitcode: " + unitcode)
        
        if subtype == '00':
            command = rfx.rfx_subtype_42_cmd00[ByteToHex(message[7])]
        elif subtype == '01':
            command = rfx.rfx_subtype_42_cmd01[ByteToHex(message[7])]
        else:
            command = '0'

        logger.debug("Command: " + command)

        signal = rfxdecode.decodeSignal(message[8])

        # PRINTOUT
        if cmdarg.printout_complete:
            logger.debug("Printout data")
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_42[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Unitcode\t\t= " + unitcode)
            logger.info("Command\t\t\t= " + command)
            logger.info("Signal level\t\t= " + str(signal))

        # CSV 
        if cmdarg.printout_csv:
            logger.debug("Output in CSV")
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s\n" %(timestamp, packettype, subtype, seqnbr, str(signal), unitcode, command))
            sys.stdout.flush()

        # TRIGGER
        if config.trigger_active:
            logger.debug("Check trigger")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$unitcode$", unitcode )
                    action = action.replace("$command$", command )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, unitcode, 0, command, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Thermostat.'+unitcode+'\ntype=command\ncurrent='+command+'\nunits=C', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Thermostat.'+unitcode+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x50 - Temperature sensors
    # ---------------------------------------
    if packettype == '50':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        temperature = rfxdecode.decodeTemperature(message[6], message[7])
        signal = rfxdecode.decodeSignal(message[8])
        battery = rfxdecode.decodeBattery(message[8])
        
        # PRINTOUT
        if cmdarg.printout_complete:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_50[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + sensor_id)
            logger.info("Temperature\t\t= " + temperature + " C")
            logger.info("Battery\t\t\t= " + str(battery))
            logger.info("Signal level\t\t= " + str(signal))

        # CSV
        if cmdarg.printout_csv:
            logger.debug("CSV Output")
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, sensor_id, str(battery), str(signal), temperature ))
            sys.stdout.flush()
            
        # TRIGGER
        if config.trigger_active:
            logger.debug("Check trigger")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$temperature$", str(temperature) )
                    action = action.replace("$battery$", str(battery) )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
                else:
                    logger.debug("No trigger match")
        
        # GRAPHITE
        if config.graphite_active == True:
            logger.debug("Send to Graphite")
            now = int( time.time() )
            linesg=[]
            linesg.append("%s.%s.temperature %s %d" % ( 'rfxcmd', sensor_id, temperature,now))
            linesg.append("%s.%s.battery %s %d" % ( 'rfxcmd', sensor_id, battery,now))
            linesg.append("%s.%s.signal %s %d"% ( 'rfxcmd', sensor_id, signal,now))
            send_graphite(config.graphite_server, config.graphite_port, linesg)
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), 0, 0, 0, 0, 0)
        
        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Temp.'+sensor_id+'\ntype=temp\ncurrent='+temperature+'\nunits=C', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Temp.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Temp.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        # WEEWX
        if config.weewx_active:
            for sensor in weewxlist.data:
                type = sensor.getElementsByTagName('type')[0].childNodes[0].nodeValue
                id = sensor.getElementsByTagName('id')[0].childNodes[0].nodeValue
                sensor_type = packettype + subtype
                if type == sensor_type and id == sensor_id:
                    logger.debug("Weewx action, Sensor type: %s, id: %s" % (str(type), str(id)))
                    wwx.wwx_0x51_temp = temperature
                    wwx.wwx_0x51_batt = battery
                    wwx.wwx_0x51_rssi = signal
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x51 - Humidity sensors
    # ---------------------------------------
    if packettype == '51':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        humidity = int(ByteToHex(message[6]),16)
        humidity_status = rfx.rfx_subtype_51_humstatus[ByteToHex(message[7])]
        signal = rfxdecode.decodeSignal(message[8])
        battery = rfxdecode.decodeBattery(message[8])
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_51[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + sensor_id)
            logger.info("Humidity\t\t= " + str(humidity))
            logger.info("Humidity Status\t\t= " + humidity_status)
            logger.info("Battery\t\t\t= " + str(battery))
            logger.info("Signal level\t\t= " + str(signal))
        
        # CSV
        if cmdarg.printout_csv:
            logger.debug("CSV Output")
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
                            (timestamp, unixtime_utc, packettype, subtype, seqnbr, sensor_id, humidity_status, str(humidity), str(battery), str(signal)) )
            sys.stdout.flush()
        
        # TRIGGER
        if config.trigger_active:
            logger.debug("Check trigger")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$humidity$", str(humidity) )
                    action = action.replace("$battery$", str(battery) )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        # GRAPHITE
        if config.graphite_active == True:
            logger.debug("Send to Graphite")
            now = int( time.time() )
            linesg=[]
            linesg.append("%s.%s.humidity %s %d" % ( 'rfxcmd', sensor_id, humidity,now))
            linesg.append("%s.%s.battery %s %d" % ( 'rfxcmd', sensor_id, battery,now))
            linesg.append("%s.%s.signal %s %d"% ( 'rfxcmd', sensor_id, signal,now))
            send_graphite(config.graphite_server, config.graphite_port, linesg)
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, humidity_status, humidity, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Hum.'+sensor_id+'\ntype=humidity\ncurrent='+str(humidity)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Hum.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Hum.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        # WEEWX
        if config.weewx_active:
            for sensor in weewxlist.data:
                type = sensor.getElementsByTagName('type')[0].childNodes[0].nodeValue
                id = sensor.getElementsByTagName('id')[0].childNodes[0].nodeValue
                sensor_type = packettype + subtype
                if type == sensor_type and id == sensor_id:
                    logger.debug("Weewx action, Sensor type: %s, id: %s" % (str(type), str(id)))
                    wwx.wwx_0x51_hum = humidity
                    wwx.wwx_0x51_batt = battery
                    wwx.wwx_0x51_rssi = signal
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x52 - Temperature and humidity sensors
    # ---------------------------------------
    if packettype == '52':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        temperature = rfxdecode.decodeTemperature(message[6], message[7])
        humidity = int(ByteToHex(message[8]),16)
        humidity_status = rfx.rfx_subtype_52_humstatus[ByteToHex(message[9])]
        signal = rfxdecode.decodeSignal(message[10])
        battery = rfxdecode.decodeBattery(message[10])
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.debug("Print data stdout")
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_52[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + sensor_id)
            logger.info("Temperature\t\t= " + temperature + " C")
            logger.info("Humidity\t\t= " + str(humidity) + "%")
            logger.info("Humidity Status\t\t= " + humidity_status)
            logger.info("Battery\t\t\t= " + str(battery))
            logger.info("Signal level\t\t= " + str(signal))
        
        # CSV
        if cmdarg.printout_csv == True:
            logger.debug("CSV Output")
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
                            (timestamp, unixtime_utc, packettype, subtype, seqnbr, sensor_id, humidity_status,
                            temperature, str(humidity), str(battery), str(signal)) )
            sys.stdout.flush()
        
        # TRIGGER
        if config.trigger_active:
            logger.debug("Check trigger")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$temperature$", str(temperature) )
                    action = action.replace("$humidity$", str(humidity) )
                    action = action.replace("$battery$", str(battery) )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # GRAPHITE
        if config.graphite_active == True:
            logger.debug("Send to Graphite")
            now = int( time.time() )
            linesg=[]
            linesg.append("%s.%s.temperature %s %d" % ( 'rfxcmd', sensor_id, temperature,now))
            linesg.append("%s.%s.humidity %s %d" % ( 'rfxcmd', sensor_id, humidity,now))
            linesg.append("%s.%s.battery %s %d" % ( 'rfxcmd', sensor_id, battery,now))
            linesg.append("%s.%s.signal %s %d"% ( 'rfxcmd', sensor_id, signal,now))
            send_graphite(config.graphite_server, config.graphite_port, linesg)
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, humidity_status, humidity, 0, 0, 0, float(temperature), 0, 0, 0, 0, 0)
        
        # XPL
        if config.xpl_active:
            logger.debug("Send to xPL")
            xpl.send(config.xpl_host, 'device=HumTemp.'+sensor_id+'\ntype=temp\ncurrent='+temperature+'\nunits=C', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=HumTemp.'+sensor_id+'\ntype=humidity\ncurrent='+str(humidity)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=HumTemp.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=HumTemp.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        # RRD
        if config.rrd_active == True:
            rfxrrd.rrd2Metrics(packettype, sensor_id, temperature, humidity, config.rrd_path)
        
        # WEEWX
        if config.weewx_active:
            for sensor in weewxlist.data:
                type = sensor.getElementsByTagName('type')[0].childNodes[0].nodeValue
                id = sensor.getElementsByTagName('id')[0].childNodes[0].nodeValue
                sensor_type = packettype + subtype
                if type == sensor_type and id == sensor_id:
                    logger.debug("Weewx action, Sensor type: %s, id: %s" % (str(type), str(id)))
                    wwx.wwx_0x52_temp = temperature
                    wwx.wwx_0x52_hum = humidity
                    wwx.wwx_0x52_batt = battery
                    wwx.wwx_0x52_rssi = signal
            
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x53 - Barometric
    # RESERVED FOR FUTURE
    # ---------------------------------------

    # ---------------------------------------
    # 0x54 - Temperature, humidity and barometric sensors
    # Credit: Jean-Baptiste Bodart
    # ---------------------------------------
    if packettype == '54':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        temperature = rfxdecode.decodeTemperature(message[6], message[7])
        humidity = int(ByteToHex(message[8]),16)
        try:
            humidity_status = rfx.rfx_subtype_54_humstatus[ByteToHex(message[9])]
        except:
            logger.debug("Humidity status [" + ByteToHex(message[9]) + "] is unknown (" + ByteToHex(message) + ")")
            humidity_status = "Unknown"
        barometric_high = ByteToHex(message[10])
        barometric_low = ByteToHex(message[11])
        barometric_high = clearBit(int(barometric_high,16),7)
        barometric_high = barometric_high << 8
        barometric = ( barometric_high + int(barometric_low,16) )
        if config.barometric != 0:
            barometric = int(barometric) + int(config.barometric)
        forecast = rfx.rfx_subtype_54_forecast[ByteToHex(message[12])]
        signal = rfxdecode.decodeSignal(message[13])
        battery = rfxdecode.decodeBattery(message[13])
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.debug("Printout")
            logger.info("Subtype\t\t\t= %s " % str(rfx.rfx_subtype_54[subtype]))
            logger.info("Seqnbr\t\t\t= %s " % str(seqnbr))
            logger.info("Id\t\t\t= %s " % str(sensor_id))
            logger.info("Temperature\t\t= %s C " % str(temperature))
            logger.info("Humidity\t\t= %s " % str(humidity))
            if not humidity_status == False:
                logger.info("Humidity Status\t\t= %s " % str(humidity_status))
            logger.info("Barometric pressure\t= %s hPa" % str(barometric))
            logger.info("Forecast Status\t\t= %s " % str(forecast))
            logger.info("Signal level\t\t= %s " % str(signal))
            logger.info("Battery\t\t\t= %s " % str(battery))
        
        # CSV
        if cmdarg.printout_csv == True:
            logger.debug("CSV")
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
                            (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(battery), str(signal), sensor_id,
                            forecast, humidity_status, str(humidity), str(barometric), str(temperature)))
            sys.stdout.flush()
        
        # TRIGGER
        if config.trigger_active:   
            logger.debug("Trigger")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$temperature$", str(temperature) )
                    action = action.replace("$humidity$", str(humidity) )
                    action = action.replace("$barometric$", str(barometric) )
                    action = action.replace("$battery$", str(battery) )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # GRAPHITE
        if config.graphite_active == True:
            logger.debug("Send to Graphite")
            now = int( time.time() )
            linesg=[]
            linesg.append("%s.%s.temperature %s %d" % ( 'rfxcmd', sensor_id, temperature,now))
            linesg.append("%s.%s.humidity %s %d" % ( 'rfxcmd', sensor_id, humidity,now))
            linesg.append("%s.%s.barometric %s %d" % ( 'rfxcmd', sensor_id, barometric,now))
            linesg.append("%s.%s.battery %s %d" % ( 'rfxcmd', sensor_id, battery,now))
            linesg.append("%s.%s.signal %s %d"% ( 'rfxcmd', sensor_id, signal,now))
            send_graphite(config.graphite_server, config.graphite_port, linesg)
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, forecast, humidity_status, humidity, barometric, 0, 0, float(temperature), 0, 0, 0, 0, 0)
        
        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=HumTempBaro.'+sensor_id+'\ntype=temp\ncurrent='+temperature+'\nunits=C', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=HumTempBaro.'+sensor_id+'\ntype=humidity\ncurrent='+str(humidity)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=HumTempBaro.'+sensor_id+'\ntype=humidity\ncurrent='+str(barometric)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=HumTempBaro.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=HumTempBaro.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        # WEEWX
        if config.weewx_active:
            for sensor in weewxlist.data:
                type = sensor.getElementsByTagName('type')[0].childNodes[0].nodeValue
                id = sensor.getElementsByTagName('id')[0].childNodes[0].nodeValue
                sensor_type = packettype + subtype
                if type == sensor_type and id == sensor_id:
                    logger.debug("Weewx action, Sensor type: %s, id: %s" % (str(type), str(id)))
                    wwx.wwx_0x54_temp = temperature
                    wwx.wwx_0x54_hum = humidity
                    wwx.wwx_0x54_baro = barometric
                    wwx.wwx_0x54_batt = battery
                    wwx.wwx_0x54_rssi = signal
         
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x55 - Rain sensors
    # ---------------------------------------
    if packettype == '55':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        rainrate_high = ByteToHex(message[6])
        rainrate_low = ByteToHex(message[7])
        if subtype == '01':
            rainrate = int(rainrate_high,16) * 0x100 + int(rainrate_low,16)
        elif subtype == '02':
            rainrate = float( int(rainrate_high,16) * 0x100 + int(rainrate_low,16) ) / 100
        else:
            rainrate = 0
        raintotal1 = ByteToHex(message[8])
        raintotal2 = ByteToHex(message[9])
        raintotal3 = ByteToHex(message[10])
        if subtype != '06':
            raintotal = float( (int(raintotal1, 16) * 0x1000) + (int(raintotal2, 16) * 0x100) + int(raintotal3, 16) ) / 10
        else:
            raintotal = 0
        signal = rfxdecode.decodeSignal(message[11])
        battery = rfxdecode.decodeBattery(message[11])
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_55[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + sensor_id)
            
            if subtype == '01' or subtype == '02':
                logger.info("Rain rate\t\t= " + str(rainrate) + " mm/hr")
            
            if subtype != '06':
                logger.info("Raintotal:\t\t= " + str(raintotal) + " mm")
            else:
                logger.info("Raintotal:\t\t= Not implemented in rfxcmd, need example data")
            
            logger.info("Battery\t\t\t= " + str(battery))
            logger.info("Signal level\t\t= " + str(signal))
        
        # CSV
        if cmdarg.printout_csv == True:
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
                            ( timestamp, unixtime_utc, packettype, subtype, seqnbr, id1, id2,
                            str(rainrate), str(int(raintotal1,16)), 
                            str(battery), str(signal) ) )
            sys.stdout.flush()
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$rainrate$", str(rainrate) )
                    action = action.replace("$raintotal$", str(raintotal) )
                    action = action.replace("$battery$", str(battery) )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # GRAPHITE
        if config.graphite_active == True:
            logger.debug("Send to Graphite")
            now = int( time.time() )
            linesg=[]
            linesg.append("%s.%s.rainrate %s %d" % ( 'rfxcmd', sensor_id, rainrate,now))
            linesg.append("%s.%s.raintotal %s %d" % ( 'rfxcmd', sensor_id, raintotal,now))
            linesg.append("%s.%s.battery %s %d" % ( 'rfxcmd', sensor_id, battery,now))
            linesg.append("%s.%s.signal %s %d"% ( 'rfxcmd', sensor_id, signal,now))
            send_graphite(config.graphite_server, config.graphite_port, linesg)
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(rainrate), float(raintotal), 0, 0, 0, 0)
        
        # WEEWX
        if config.weewx_active:
            for sensor in weewxlist.data:
                type = sensor.getElementsByTagName('type')[0].childNodes[0].nodeValue
                id = sensor.getElementsByTagName('id')[0].childNodes[0].nodeValue
                sensor_type = packettype + subtype
                if type == sensor_type and id == sensor_id:
                    logger.debug("Weewx action, Sensor type: %s, id: %s" % (str(type), str(id)))
                    wwx.wwx_0x55_rainrate = rainrate
                    wwx.wwx_0x55_raintotal = raintotal
                    wwx.wwx_0x55_batt = battery
                    wwx.wwx_0x55_rssi = signal
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
    
    # ---------------------------------------
    # 0x56 - Wind sensors
    # ---------------------------------------
    if packettype == '56':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        direction = ( ( int(ByteToHex(message[6]),16) * 256 ) + int(ByteToHex(message[7]),16) )
        if subtype != "05":
            av_speed = ( ( int(ByteToHex(message[8]),16) * 256 ) + int(ByteToHex(message[9]),16) ) * 0.1
        else:
            av_speed = 0;
        gust = ( ( int(ByteToHex(message[10]),16) * 256 ) + int(ByteToHex(message[11]),16) ) * 0.1
        if subtype == "04":
            temperature = rfxdecode.decodeTemperature(message[12], message[13])
        else:
            temperature = 0
        if subtype == "04":
            windchill = rfxdecode.decodeTemperature(message[14], message[15])
        else:
            windchill = 0
        signal = rfxdecode.decodeSignal(message[16])
        battery = rfxdecode.decodeBattery(message[16])
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_56[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + sensor_id)
            logger.info("Wind direction\t\t= " + str(direction) + " degrees")
            if subtype != "05":
                logger.info("Average wind\t\t= " + str(av_speed) + " mtr/sec")
            if subtype == "04":
                logger.info("Temperature\t\t= " + str(temperature) + " C")
                logger.info("Wind chill\t\t= " + str(windchill) + " C" )
            logger.info("Windgust\t\t= " + str(gust) + " mtr/sec")
            logger.info("Battery\t\t\t= " + str(battery))
            logger.info("Signal level\t\t= " + str(signal))
        
        # CSV
        if cmdarg.printout_csv == True:
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
                            (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(battery), str(signal), sensor_id, str(temperature), str(av_speed), str(gust), str(direction), str(windchill) ) )
            sys.stdout.flush()
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$direction$", str(direction) )
                    if subtype != "05":
                        action = action.replace("$average$", str(av_speed) )
                    if subtype == "04":
                        action = action.replace("$temperature$", str(temperature) )
                        action = action.replace("$windchill$", str(windchill) )
                    action = action.replace("$windgust$", str(gust) )
                    action = action.replace("$battery$", str(battery) )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # GRAPHITE
        if config.graphite_active == True:
            logger.debug("Send to Graphite")
            now = int( time.time() )
            linesg=[]
            linesg.append("%s.%s.direction %s %d" % ( 'rfxcmd', sensor_id, direction,now))
            if subtype != "05":
                linesg.append("%s.%s.average %s %d" % ( 'rfxcmd', sensor_id, av_speed,now))
            if subtype == "04":
                linesg.append("%s.%s.chill %s %d" % ( 'rfxcmd', sensor_id, windchill,now))
                linesg.append("%s.%s.temperature %s %d" % ( 'rfxcmd', sensor_id, temperature,now))
            linesg.append("%s.%s.gust %s %d" % ( 'rfxcmd', sensor_id, gust, now))
            linesg.append("%s.%s.battery %s %d" % ( 'rfxcmd', sensor_id, battery, now))
            linesg.append("%s.%s.signal %s %d"% ( 'rfxcmd', sensor_id, signal, now))
            send_graphite(config.graphite_server, config.graphite_port, linesg)
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, 0, 0, float(temperature), av_speed, gust, direction, float(windchill), 0)
        
        # xPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=direction\ncurrent='+str(direction)+'\nunits=Degrees', config.xpl_sourcename, config.xpl_includehostname)
            
            if subtype != "05":
                xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=Averagewind\ncurrent='+str(av_speed)+'\nunits=mtr/sec', config.xpl_sourcename, config.xpl_includehostname)
            
            if subtype == "04":
                xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=temperature\ncurrent='+str(temperature)+'\nunits=C', config.xpl_sourcename, config.xpl_includehostname)
                xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=windchill\ncurrent='+str(windchill)+'\nunits=C', config.xpl_sourcename, config.xpl_includehostname)
            
            xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=windgust\ncurrent='+str(gust)+'\nunits=mtr/sec', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Wind.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        # WEEWX
        if config.weewx_active:
            for sensor in weewxlist.data:
                type = sensor.getElementsByTagName('type')[0].childNodes[0].nodeValue
                id = sensor.getElementsByTagName('id')[0].childNodes[0].nodeValue
                sensor_type = packettype + subtype
                if type == sensor_type and id == sensor_id:
                    logger.debug("Weewx action, Sensor type: %s, id: %s" % (str(type), str(id)))
                    wwx.wwx_0x56_direction = direction
                    if subtype != "05":
                        wwx.wwx_0x56_avspeed = av_speed
                    else:
                        wwx.wwx_0x56_avspeed = "None"
                    if subtype == "04":
                        wwx.wwx_0x56_temp = temperature
                        wwx.wwx_0x56_chill = windchill
                    else:
                        wwx.wwx_0x56_temp = "None"
                        wwx.wwx_0x56_chill = "None"
                    wwx.wwx_0x56_gust = gust
                    wwx.wwx_0x56_batt = battery
                    wwx.wwx_0x56_rssi = signal
            
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x57 UV Sensor
    # ---------------------------------------
    if packettype == '57':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        uv = int(ByteToHex(message[6]), 16) * 10
        temperature = rfxdecode.decodeTemperature(message[6], message[8])
        signal = rfxdecode.decodeSignal(message[9])
        battery = rfxdecode.decodeBattery(message[9])
            
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.debug("Printout action")
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_57[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + sensor_id)
            logger.info("UV\t\t\t= " + str(uv))
            if subtype == '03':
                logger.info("Temperature\t\t= " + temperature + " C")
            logger.info("Battery\t\t\t= " + str(battery))
            logger.info("Signal level\t\t= " + str(signal))
        
        # CSV
        if cmdarg.printout_csv:
            logger.debug("CSVout action")
            if subtype == '03':
                sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, sensor_id, str(uv), temperature, str(battery), str(signal) ) )
            else:
                sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, sensor_id, str(uv), str(battery), str(signal) ) )
            sys.stdout.flush()
        
        # TRIGGER
        if config.trigger_active:
            logger.debug("Trigger action")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$uv$", str(uv) )
                    if subtype == '03':
                        action = action.replace("$temperature$", str(temperature) )
                    action = action.replace("$battery$", str(battery) )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # GRAPHITE
        if config.graphite_active == True:
            logger.debug("Graphite action")
            now = int( time.time() )
            linesg=[]
            if subtype == "03":
                linesg.append("%s.%s.temperature %s %d" % ( 'rfxcmd', sensor_id, temperature,now))
            linesg.append("%s.%s.uv %s %d" % ( 'rfxcmd', sensor_id, uv,now))
            linesg.append("%s.%s.battery %s %d" % ( 'rfxcmd', sensor_id, battery,now))
            linesg.append("%s.%s.signal %s %d"% ( 'rfxcmd', sensor_id, signal,now))
            send_graphite(config.graphite_server, config.graphite_port, linesg)
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            logger.debug("Database action")
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, str(uv), 0, 0, 0, float(temperature), 0, 0, 0, 0, 0)
        
        # xPL
        if config.xpl_active:
            logger.debug("xPL action")
            xpl.send(config.xpl_host, 'device=UV.'+sensor_id+'\ntype=uv\ncurrent='+str(uv)+'\nunits=Index', config.xpl_sourcename, config.xpl_includehostname)
            if subtype == "03":
                xpl.send(config.xpl_host, 'device=UV.'+sensor_id+'\ntype=Temperature\ncurrent='+str(temperature)+'\nunits=Celsius', config.xpl_sourcename, config.xpl_includehostname)
        
        # WEEWX
        if config.weewx_active:
            for sensor in weewxlist.data:
                type = sensor.getElementsByTagName('type')[0].childNodes[0].nodeValue
                id = sensor.getElementsByTagName('id')[0].childNodes[0].nodeValue
                sensor_type = packettype + subtype
                if type == sensor_type and id == sensor_id:
                    logger.debug("Weewx action, Sensor type: %s, id: %s" % (str(type), str(id)))
                    wwx.wwx_0x57_uv = uv
                    if subtype == "03":
                        wwx.wwx_0x57_temp = temperature
                    else:
                        wwx.wwx_0x57_temp = "None"
                    wwx.wwx_0x57_batt = battery
                    wwx.wwx_0x57_rssi = signal
            
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x58 Date/Time sensor
    # ---------------------------------------
    if packettype == '58':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        date_yy = int(ByteToHex(message[6]), 16)
        date_mm = int(ByteToHex(message[7]), 16)
        date_dd = int(ByteToHex(message[8]), 16)
        date_string = "20%s-%s-%s" % (str(date_yy).zfill(2), str(date_mm).zfill(2), str(date_dd).zfill(2))
        date_dow = int(ByteToHex(message[9]), 16)
        time_hr = int(ByteToHex(message[10]), 16)
        time_min = int(ByteToHex(message[11]), 16)
        time_sec = int(ByteToHex(message[12]), 16)
        time_string = "%s:%s:%s" % (str(time_hr), str(time_min), str(time_sec))
        datetime_string = "%s %s" % (str(date_string), str(time_string))
        logger.debug("DateTime: %s" % str(datetime_string))
        signal = rfxdecode.decodeSignal(message[13])
        battery = rfxdecode.decodeBattery(message[13])
            
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.debug("Printout action")
            logger.info("Subtype\t\t\t= %s" % str(rfx.rfx_subtype_58[subtype]))
            logger.info("Seqnbr\t\t\t= %s" % str(seqnbr))
            logger.info("Id\t\t\t= %s" % str(sensor_id))
            logger.info("Time\t\t\t= %s" % str(time_string))
            logger.info("Date (yy-mm-dd)\t\t= %s" % str(date_string))
            logger.info("Day of week (1-7)\t= %s" % str(date_dow))
            logger.info("Battery\t\t\t= %s" % str(battery))
            logger.info("Signal level\t\t= %s" % str(signal))
        
        # CSV
        if cmdarg.printout_csv:
            logger.debug("CSVout action")
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, packettype, subtype, seqnbr, sensor_id, str(time_string), str(date_string), str(date_dow), str(battery), str(signal) ) )
            sys.stdout.flush()
        
        # TRIGGER
        if config.trigger_active:
            logger.debug("Trigger action")
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$date$", str(date_string) )
                    action = action.replace("$time$", str(time_string) )
                    action = action.replace("$dow$", str(date_dow) )
                    action = action.replace("$battery$", str(battery) )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            logger.debug("Database action")
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, str(date_dow), 0, 0, 0, 0, 0, 0, 0, 0, str(datetime_string))
        
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
    
    # ---------------------------------------
    # 0x59 Current Sensor
    # ---------------------------------------
    if packettype == '59':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
    
        # DATA
        sensor_id = id1 + id2
        count = int(ByteToHex(message[6]),16)
        channel1 = (int(ByteToHex(message[7]),16) * 0x100 + int(ByteToHex(message[8]),16)) * 0.1
        channel2 = (int(ByteToHex(message[9]),16) * 0x100 + int(ByteToHex(message[10]),16)) * 0.1
        channel3 = (int(ByteToHex(message[11]),16) * 0x100 + int(ByteToHex(message[12]),16)) * 0.1
        signal = rfxdecode.decodeSignal(message[13])
        battery = rfxdecode.decodeBattery(message[13])
    
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_5A[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + sensor_id)
            logger.info("Counter\t\t\t= " + str(count))
            logger.info("Channel 1\t\t= " + str(channel1) + "A")
            logger.info("Channel 2\t\t= " + str(channel2) + "A")
            logger.info("Channel 3\t\t= " + str(channel3) + "A")
            logger.info("Battery\t\t\t= " + str(battery))
            logger.info("Signal level\t\t= " + str(signal))
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$counter$", str(count) )
                    action = action.replace("$channel1$", str(channel1) )
                    action = action.replace("$channel2$", str(channel2) )
                    action = action.replace("$channel3$", str(channel3) )
                    action = action.replace("$battery$", str(battery) )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=channel1\ncurrent='+str(channel1)+'\nunits=A', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=channel2\ncurrent='+str(channel2)+'\nunits=A', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=channel3\ncurrent='+str(channel3)+'\nunits=A', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")

    # ---------------------------------------
    # 0x5A Energy sensor
    # Credit: Jean-Michel ROY
    # ---------------------------------------
    if packettype == '5A':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        signal = rfxdecode.decodeSignal(message[17])
        count = int(ByteToHex(message[6]), 16)
        battery = rfxdecode.decodeBattery(message[17])
        instant = int(ByteToHex(message[7]), 16) * 0x1000000 + int(ByteToHex(message[8]), 16) * 0x10000 + int(ByteToHex(message[9]), 16) * 0x100  + int(ByteToHex(message[10]), 16)
        usage = int ((int(ByteToHex(message[11]), 16) * 0x10000000000 + int(ByteToHex(message[12]), 16) * 0x100000000 +int(ByteToHex(message[13]), 16) * 0x1000000 + int(ByteToHex(message[14]), 16) * 0x10000 + int(ByteToHex(message[15]), 16) * 0x100 + int(ByteToHex(message[16]), 16) ) / 223.666)
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_5A[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + sensor_id)
            logger.info("Count\t\t\t= " + str(count))
            logger.info("Instant usage\t\t= " + str(instant) + " Watt")
            logger.info("Total usage\t\t= " + str(usage) + " Wh")
            logger.info("Battery\t\t\t= " + str(battery))
            logger.info("Signal level\t\t= " + str(signal))
        
        # CSV
        if cmdarg.printout_csv == True:
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
                            (timestamp, unixtime_utc, packettype, subtype, seqnbr, sensor_id,
                            str(instant), str(usage), str(battery), str(signal)) )
            sys.stdout.flush()
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$count$", str(count) )
                    action = action.replace("$instant$", str(instant) )
                    action = action.replace("$total$", str(usage) )
                    action = action.replace("$battery$", str(battery) )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, count, 0, 0, 0, float(instant), 0, 0,float(usage), 0, 0)
        
        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Energy.'+sensor_id+'\ntype=instant_usage\ncurrent='+str(instant)+'\nunits=W', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Energy.'+sensor_id+'\ntype=total_usage\ncurrent='+str(usage)+'\nunits=Wh', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Energy.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Energy.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        # RRD
        if config.rrd_active == True:
            rfxrrd.rrd1Metric(packettype, sensor_id, instant, config.rrd_path)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x5B Current Sensor
    # ---------------------------------------
    if packettype == '5B':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        count = int(ByteToHex(message[6]),16)
        channel1 = (int(ByteToHex(message[7]),16) * 0x100 + int(ByteToHex(message[8]),16)) * 0.1
        channel2 = (int(ByteToHex(message[9]),16) * 0x100 + int(ByteToHex(message[10]),16)) * 0.1
        channel3 = (int(ByteToHex(message[11]),16) * 0x100 + int(ByteToHex(message[12]),16)) * 0.1
        total = float ((int(ByteToHex(message[13]), 16) * 0x10000000000 + int(ByteToHex(message[14]), 16) * 0x100000000 +int(ByteToHex(message[15]), 16) * 0x1000000 + int(ByteToHex(message[16]), 16) * 0x10000 + int(ByteToHex(message[17]), 16) * 0x100 + int(ByteToHex(message[18]), 16) ) / 223.666)
        signal = rfxdecode.decodeSignal(message[19])
        battery = rfxdecode.decodeBattery(message[19])
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_5B[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + sensor_id)
            logger.info("Counter\t\t\t= " + str(count))
            logger.info("Channel 1\t\t= " + str(channel1) + "A")
            logger.info("Channel 2\t\t= " + str(channel2) + "A")
            logger.info("Channel 3\t\t= " + str(channel3) + "A")
            if total != 0:
                logger.info("Total\t\t\t= %s Wh" % str(round(total,1)))
            logger.info("Battery\t\t\t= " + str(battery))
            logger.info("Signal level\t\t= " + str(signal))
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$counter$", str(count) )
                    action = action.replace("$channel1$", str(channel1) )
                    action = action.replace("$channel2$", str(channel2) )
                    action = action.replace("$channel3$", str(channel3) )
                    action = action.replace("$battery$", str(battery) )
                    action = action.replace("$signal$", str(signal) )
                    action = action.replace("$total$", str(total) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, count, 0, 0, 0, float(channel1), float(channel2), float(channel3), float(total), 0, 0)
        
        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=channel1\ncurrent='+str(channel1)+'\nunits=A', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=channel2\ncurrent='+str(channel2)+'\nunits=A', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=channel3\ncurrent='+str(channel3)+'\nunits=A', config.xpl_sourcename, config.xpl_includehostname)
            if total != 0:
                xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=total\ncurrent='+str(total)+'\nunits=Wh', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=battery\ncurrent='+str(battery*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
    
    # ---------------------------------------
    # 0x5C Power Sensors
    # ---------------------------------------
    if packettype == '5C':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        voltage = int(ByteToHex(message[6]),16)
        current = (int(ByteToHex(message[7]),16) * 0x100 + int(ByteToHex(message[8]),16)) * 0.01
        power = (int(ByteToHex(message[9]),16) * 0x100 + int(ByteToHex(message[10]),16)) * 0.1
        energy = (int(ByteToHex(message[11]),16) * 0x100 + int(ByteToHex(message[12]),16)) * 0.01
        powerfactor = (int(ByteToHex(message[13]), 16)) * 0.01
        freq = int(ByteToHex(message[14]), 16)
        signal = rfxdecode.decodeSignal(message[15])
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= %s" % str(rfx.rfx_subtype_5C[subtype]))
            logger.info("Seqnbr\t\t\t= %s" % str(seqnbr))
            logger.info("Id\t\t\t= %s" % str(sensor_id))
            logger.info("Voltage\t\t\t= %s Volt" % (str(voltage)))
            logger.info("Current\t\t\t= %s Ampere" % str(current))
            logger.info("Instant power\t\t= %s Watt" % str(power))
            logger.info("Total usage\t\t= %s kWh" % str(energy))
            logger.info("Power factor\t\t= %s " % str(powerfactor))
            logger.info("Frequency\t\t= %s Hz" % str(freq))
            logger.info("Signal level\t\t= %s" % str(signal))
            
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", str(sensor_id) )
                    action = action.replace("$voltage$", str(voltage) )
                    action = action.replace("$current$", str(current) )
                    action = action.replace("$instantpower$", str(instantpower) )
                    action = action.replace("$totalusage$", str(totalusage) )
                    action = action.replace("$powerfactor$", str(powerfactor) )
                    action = action.replace("$frequency$", str(freq) )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, battery, signal, sensor_id, 0, 0, 0, 0, voltage, freq, float(instantpower), float(current), float(powerfactor), float(totalusage), 0, 0)
        
        # XPL
        if config.xpl_active:
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=voltage\ncurrent='+str(channel1)+'\nunits=V', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=current\ncurrent='+str(channel2)+'\nunits=A', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=instantpower\ncurrent='+str(channel3)+'\nunits=Watt', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=totalusage\ncurrent='+str(channel3)+'\nunits=kWh', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=powerfactor\ncurrent='+str(channel3)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=frequency\ncurrent='+str(channel3)+'\nunits=Hz', config.xpl_sourcename, config.xpl_includehostname)
            xpl.send(config.xpl_host, 'device=Current.'+sensor_id+'\ntype=signal\ncurrent='+str(signal*10)+'\nunits=%', config.xpl_sourcename, config.xpl_includehostname)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
    
    # ---------------------------------------
    # 0x5E Gas Usage Sensor
    # ---------------------------------------
    if packettype == '5E':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        
        decoded = True
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_5E[subtype])
            logger.info("Not implemented in RFXCMD, please send sensor data to sebastian.sjoholm@gmail.com")
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
    
    # ---------------------------------------
    # 0x5F Water Usage Sensor
    # ---------------------------------------
    if packettype == '5F':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        
        decoded = True
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_5F[subtype])
            logger.info("Not implemented in RFXCMD, please send sensor data to sebastian.sjoholm@gmail.com")
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
    
    # ---------------------------------------
    # 0x70 RFXsensor
    # ---------------------------------------
    if packettype == '70':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        decoded = True
        
        # DATA
        if subtype == '00':
            temperature = float(rfxdecode.decodeTemperature(message[5], message[6]))
            temperature = temperature * 0.1
        else:
            temperature = 0
        if subtype == '01' or subtype == '02':
            voltage_hi = int(ByteToHex(message[5]), 16) * 256
            voltage_lo = int(ByteToHex(message[6]), 16)
            voltage = voltage_hi + voltage_lo
        else:
            voltage = 0
        signal = rfxdecode.decodeSignal(message[7])
        
        if subtype == '03':
            sensor_message = rfx.rfx_subtype_70_msg03[message[6]]
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_70[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + id1)
        
            if subtype == '00':
                logger.info("Temperature\t\t= " + str(temperature) + " C")
            
            if subtype == '01' or subtype == '02':
                logger.info("Voltage\t\t\t= " + str(voltage) + " mV")
            
            if subtype == '03':
                logger.info("Message\t\t\t= " + sensor_message)
            
            logger.info("Signal level\t\t= " + str(signal))
            
        # CSV
        if cmdarg.printout_csv == True:
            if subtype == '00':
                sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), id1, str(temperature)))
            if subtype == '01' or subtype == '02':
                sys.stdout.write("%s;%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, str(signal), id1, str(voltage)))
            sys.stdout.flush()
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", id1 )
                    if subtype == '00':
                        action = action.replace("$temperature$", str(temperature) )
                    if subtype == '01' or subtype == '02':
                        action = action.replace("$voltage$", str(voltage) )
                    if subtype == '03':
                        action = action.replace("$message$", sensor_message )
                    action = action.replace("$signal$", str(signal) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
                    
        # DATABASE
        if config.mysql_active or config.sqlite_active or config.pgsql_active:
            insert_database(timestamp, unixtime_utc, packettype, subtype, seqnbr, 255, signal, id1, ByteToHex(message[5]), ByteToHex(message[6]), 0, 0, 0, voltage, float(temperature), 0, 0, 0, 0, 0)
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
        
    # ---------------------------------------
    # 0x71 RFXmeter
    # ---------------------------------------
    if packettype == '71':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        
        decoded = True
        
        # DATA
        sensor_id = id1 + id2
        sensor_power = ''
        
        try:
            sensor_power = rfxdecode.decodePower(message[7], message[8], message[9])
        except Exception, e:
            logger.error("Exception: %s" % str(e))
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_71[subtype])
            logger.info("Seqnbr\t\t\t= " + seqnbr)
            logger.info("Id\t\t\t= " + id1)
            logger.info("Power\t\t\t= " + str(sensor_power))
            
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    action = action.replace("$id$", id1 )
                    action = action.replace("$power$", str(sensor_power) )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
            
        # CSV
        if cmdarg.printout_csv == True:
            sys.stdout.write("%s;%s;%s;%s;%s;%s;%s\n" % (timestamp, unixtime_utc, packettype, subtype, seqnbr, id1 + id2, str(sensor_power)))
            sys.stdout.flush()
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
    
    # ---------------------------------------
    # 0x72 FS20
    # ---------------------------------------
    if packettype == '72':
        logger.debug("Decode packetType 0x" + str(packettype) + " - Start")
        
        decoded = True
        
        # PRINTOUT
        if cmdarg.printout_complete == True:
            logger.info("Subtype\t\t\t= " + rfx.rfx_subtype_72[subtype])
            logger.info("Not implemented in RFXCMD, please send sensor data to sebastian.sjoholm@gmail.com")
        
        # TRIGGER
        if config.trigger_active:
            for trigger in triggerlist.data:
                trigger_message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
                action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
                rawcmd = ByteToHex ( message )
                rawcmd = rawcmd.replace(' ', '')
                if re.match(trigger_message, rawcmd):
                    logger.debug("Trigger match")
                    logger.debug("Message: " + trigger_message + ", Action: " + action)
                    action = action.replace("$raw$", raw_message )
                    action = action.replace("$packettype$", packettype )
                    action = action.replace("$subtype$", subtype )
                    logger.debug("Execute shell")
                    command = Command(action)
                    command.run(timeout=config.trigger_timeout)
                    if config.trigger_onematch:
                        logger.debug("Trigger onematch active, exit trigger")
                        return
        
        logger.debug("Decode packetType 0x" + str(packettype) + " - End")
    
    # ---------------------------------------
    # Not decoded message
    # ---------------------------------------   
    
    # The packet is not decoded, then logger.info(it on the screen)
    if decoded == False:
        logger.error("Message not decoded. Line: " + _line())
        logger.error("Message: " + ByteToHex(message))
        logger.info(timestamp + " " + ByteToHex(message))
        logger.info("RFXCMD cannot decode message, see http://code.google.com/p/rfxcmd/wiki/ for more information.")
    
    # decodePackage END
    return

# ----------------------------------------------------------------------------
    
def read_socket():
    """
    Check socket for messages
    
    Credit: Olivier Djian
    """

    global messageQueue
    
    if not messageQueue.empty():
        logger.debug("Message received in socket messageQueue")
        message = stripped(messageQueue.get())
        
        if message[0:5] == "WEEWX":
            logger.debug("Message from WEEWX [v2]")
        
        elif test_rfx( message ):
        
            if config.serial_active:
                # Flush buffer
                serial_param.port.flushOutput()
                logger.debug("SerialPort flush output")
                serial_param.port.flushInput()
                logger.debug("SerialPort flush input")
            
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            
            if message == '0A1100FF001100FF001100':
                logger.debug("Message from WEEWX")
                if cmdarg.printout_complete == True:
                    logger.info("------------------------------------------------")
                    logger.info("Request received from WEEWX station-driver")
                    logger.info("Request skipped here!")
                    
            else:           
                if cmdarg.printout_complete == True:
                    logger.info("------------------------------------------------")
                    logger.info("Incoming message from socket")
                    logger.info("Send\t\t\t= " + ByteToHex( message.decode('hex') ))
                    logger.info("Date/Time\t\t= " + timestamp)
                    logger.info("Packet Length\t\t= " + ByteToHex( message.decode('hex')[0] ))
                    
                try:
                    logger.debug("Decode message")
                    decodePacket( message.decode('hex') )
                except KeyError:
                    logger.error("Unrecognizable packet. Line: " + _line())
                    if cmdarg.printout_complete == True:
                        logger.error("Error: unrecognizable packet")
            
                if config.serial_active:
                    logger.debug("Write message to serial port")
                    serial_param.port.write( message.decode('hex') )
            
        else:
            logger.error("Invalid message from socket. Line: " + _line())
            if cmdarg.printout_complete == True:
                logger.info("------------------------------------------------")
                logger.info("Invalid message from socket")

# ----------------------------------------------------------------------------

def test_rfx( message ):
    """
    Test, filter and verify that the incoming message is valid
    Return true if valid, False if not
    """

    logger.debug("Test message: " + message)
        
    # Remove all invalid characters
    message = stripped(message)
    
    # Remove any whitespaces
    try:
        message = message.replace(' ', '')
    except Exception:
        logger.error("Error: Removing white spaces")
        return False
    
    # Test the string if it is hex format
    try:
        int(message,16)
    except Exception:
        logger.error("Error: Packet not hex format")
        return False
    
    # Check that length is even
    if len(message) % 2:
        logger.error("Error: Packet length not even")
        return False
    
    # Check that first byte is not 00
    if ByteToHex(message.decode('hex')[0]) == "00":
        logger.error("Error: Packet first byte is 00")
        return False
    
    # Length more than one byte
    if not len(message.decode('hex')) > 1:
        logger.error("Error: Packet is not longer than one byte")
        return False
    
    # Check if string is the length that it reports to be
    cmd_len = int( ByteToHex( message.decode('hex')[0]),16 )
    if not len(message.decode('hex')) == (cmd_len + 1):
        logger.error("Error: Packet length is not valid")
        return False

    logger.debug("Message OK")

    return True
            
# ----------------------------------------------------------------------------

def send_rfx( message ):
    """
    Decode and send raw message to RFX device
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    if cmdarg.printout_complete == True:
        logger.info("------------------------------------------------")
        logger.info("Send\t\t\t= " + ByteToHex( message ))
        logger.info("Date/Time\t\t= " + timestamp)
        logger.info("Packet Length\t\t= " + ByteToHex( message[0] ))
        
        try:
            decodePacket( message )
        except KeyError:
            logger.error("Error: unrecognizable packet")
    
    serial_param.port.write( message )
    time.sleep(1)

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
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                logger.debug("Timestamp: " + timestamp)
                logger.debug("SerWaiting: " + str(serial_param.port.inWaiting()))
                byte = serial_param.port.read()
                logger.debug("Byte: " + str(ByteToHex(byte)))
        except IOError, err:
            logger.error("Error: " + str(err))
            logger.error("Serial read error: %s, Line: %s" % (str(err),_line()))
        
        if byte:
            message = byte + readbytes( ord(byte) )
            logger.debug("Message: " + str(ByteToHex(message)))
            
            # First byte indicate length of message, must be other than 00
            if ByteToHex(message[0]) != "00":
            
                # Verify length
                logger.debug("Verify length")
                if (len(message) - 1) == ord(message[0]):
                
                    logger.debug("Length OK")
                    
                    # Whitelist
                    if config.whitelist_active:
                    
                        logger.debug("Check whitelist")
                        whitelist_match = False
                        for sensor in whitelist.data:
                            sensor = sensor.childNodes[0].nodeValue
                            logger.debug("Tag: " + sensor)
                            rawcmd = ByteToHex ( message )
                            rawcmd = rawcmd.replace(' ', '')
                            if re.match(sensor, rawcmd):
                                logger.debug("Whitelist match")
                                whitelist_match = True
                                pass
                    
                        if whitelist_match == False:
                            if cmdarg.printout_complete:
                                logger.info("Sensor not included in whitelist")
                            logger.debug("No match in whitelist, no process")
                            return rawcmd
                    
                    if cmdarg.printout_complete == True:
                        logger.info("------------------------------------------------")
                        logger.info("Received\t\t= " + ByteToHex( message ))
                        logger.info("Date/Time\t\t= " + timestamp)
                        logger.info("Packet Length\t\t= " + ByteToHex( message[0] ))
                    
                    logger.debug('Decode packet')
                    try:
                        decodePacket( message )
                    except KeyError:
                        logger.error("Error: unrecognizable packet (" + ByteToHex(message) + ") Line: " + _line())
                        if cmdarg.printout_complete == True:
                            logger.error("Error: unrecognizable packet")
                    
                    rawcmd = ByteToHex ( message )
                    rawcmd = rawcmd.replace(' ', '')
                    
                    return rawcmd
                
                else:
                    logger.error("Error: Incoming packet not valid length. Line: "  + _line())
                    if cmdarg.printout_complete == True:
                        logger.info("------------------------------------------------")
                        logger.info("Received\t\t= " + ByteToHex( message ))
                        logger.info("Incoming packet not valid, waiting for next...")
                
    except OSError:
        logger.error("Error in message: " + str(ByteToHex(message)) + " Line: " + _line())
        logger.error("Traceback: " + traceback.format_exc())
        logger.info("------------------------------------------------")
        logger.info("Received\t\t= " + ByteToHex( message ))
        traceback.format_exc()

# ----------------------------------------------------------------------------

def read_config( configFile, configItem):
    """
    Read item from the configuration file
    """
    logger.debug('Open configuration file')
    logger.debug('File: ' + configFile)
    
    if os.path.exists( configFile ):

        #open the xml file for reading:
        f = open( configFile,'r')
        data = f.read()
        f.close()
    
        # xml parse file data
        logger.debug('Parse config XML data')
        try:
            dom = minidom.parseString(data)
        except:
            logger.error("Error: problem in the config.xml file, cannot process it")
            logger.debug('Error in config.xml file')
            
        # Get config item
        logger.debug('Get the configuration item: ' + configItem)
        
        try:
            xmlTag = dom.getElementsByTagName( configItem )[0].toxml()
            logger.debug('Found: ' + xmlTag)
            xmlData = xmlTag.replace('<' + configItem + '>','').replace('</' + configItem + '>','')
            logger.debug('--> ' + xmlData)
        except:
            logger.debug('The item tag not found in the config file')
            xmlData = ""
            
        logger.debug('Return')
        
    else:
        logger.error("Error: Config file does not exists. Line: " + _line())
        
    return xmlData

# ----------------------------------------------------------------------------

def read_whitelistfile():
    """
    Read whitelist file to list
    """
    try:
        xmldoc = minidom.parse( config.whitelist_file )
    except:
        logger.error("Error in " + config.whitelist_file + " file")
        sys.exit(1)

    whitelist.data = xmldoc.documentElement.getElementsByTagName('sensor')

    for sensor in whitelist.data:
        logger.debug("Tags: " + sensor.childNodes[0].nodeValue)
        
# ----------------------------------------------------------------------------

def read_triggerfile():
    """
    Read trigger file to list
    """
    try:
        xmldoc = minidom.parse( config.trigger_file )
    except:
        logger.error("Error in " + config.trigger_file + " file")
        sys.exit(1)

    triggerlist.data = xmldoc.documentElement.getElementsByTagName('trigger')

    for trigger in triggerlist.data:
        message = trigger.getElementsByTagName('message')[0].childNodes[0].nodeValue
        action = trigger.getElementsByTagName('action')[0].childNodes[0].nodeValue
        logger.debug("Message: " + message + ", Action: " + action)

# ----------------------------------------------------------------------------

def read_weewxfile():
    """
    Read weewx file to list
    """
    try:
        xmldoc = minidom.parse( config.weewx_config )
    except:
        logger.error("Error in " + config.weewx_config + " file")
        sys.exit(1)

    weewxlist.data = xmldoc.documentElement.getElementsByTagName('sensor')

    for sensor in weewxlist.data:
        type = sensor.getElementsByTagName('type')[0].childNodes[0].nodeValue
        id = sensor.getElementsByTagName('id')[0].childNodes[0].nodeValue
        logger.debug("Type: " + type + ", id: " + id)

# ----------------------------------------------------------------------------

def print_version():
    """
    Print RFXCMD version, build and date
    """
    logger.debug("print_version")
    logger.info("RFXCMD Version: " + __version__)
    logger.info(__date__.replace('$', ''))
    logger.debug("Exit 0")
    sys.exit(0)

# ----------------------------------------------------------------------------

def check_pythonversion():
    """
    Check python version
    """
    if sys.hexversion < 0x02060000:
        logger.error("Error: Your Python need to be 2.6 or newer, please upgrade.")
        sys.exit(1)

# ----------------------------------------------------------------------------

def option_simulate(indata):
    """
    Simulate incoming packet, decode and process
    """

    # Remove all spaces
    for x in whitespace:
        indata = indata.replace(x,"")
    
    # Cut into hex chunks
    try:
        message = indata.decode("hex")
    except:
        logger.error("Error: the input data is not valid. Line: " + _line())
        logger.error("Error: the input data is not valid")
        sys.exit(1)
    
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    # Whitelist
    if config.whitelist_active:
        logger.debug("Check whitelist")
        whitelist_match = False
        for sensor in whitelist.data:
            sensor = sensor.getElementsByTagName('sensor')[0].childNodes[0].nodeValue
            logger.debug("Sensor: " + sensor)
            rawcmd = ByteToHex ( message )
            rawcmd = rawcmd.replace(' ', '')
            if re.match(sensor, rawcmd):
                whitelist_match = True
        
        if whitelist_match == False:
            if cmdarg.printout_complete:
                logger.info("Sensor not included in whitelist")
            logger.debug("No match in whitelist")
            logger.debug("Exit 0")
            sys.exit(0)

    # Printout
    if cmdarg.printout_complete:
        logger.info("------------------------------------------------")
        logger.info("Received\t\t= " + indata)
        logger.info("Date/Time\t\t= " + timestamp)
    
    # Verify that the incoming value is hex
    try:
        hexval = int(indata, 16)
    except:
        logger.error("Error: the input data is invalid hex value. Line: " + _line())
        logger.error("Error: the input data is invalid hex value")
        sys.exit(1)
                
    # Decode it
    try:
        decodePacket( message )
    except Exception as err:
        logger.error("Error: unrecognizable packet (" + ByteToHex(message) + ") Line: " + _line())
        logger.error("Error: %s" %err)
        logger.error("Error: unrecognizable packet")
        
    logger.debug('Exit 0')
    sys.exit(0)

# ----------------------------------------------------------------------------

def option_listen():
    """
    Listen to RFXtrx device and process data, exit with CTRL+C
    """
    logger.debug("Start listening...")
    
    if config.serial_active:
        logger.debug("Open serial port")
        open_serialport()

    if config.socketserver:
        try:
            serversocket = RFXcmdSocketAdapter(config.sockethost,int(config.socketport))
        except:
            logger.error("Error starting socket server. Line: " + _line())
            logger.error("Error: can not start server socket, another instance already running?")
            exit(1)
        if serversocket.netAdapterRegistered:
            logger.debug("Socket interface started")
        else:
            logger.warning("Cannot start socket interface")

    if config.serial_active:
        # Flush buffer
        logger.debug("Serialport flush output")
        serial_param.port.flushOutput()
        logger.debug("Serialport flush input")
        serial_param.port.flushInput()

        # Send RESET
        logger.debug("Send rfxcmd_reset (" + rfxcmd.reset + ")")
        serial_param.port.write( rfxcmd.reset.decode('hex') )
        logger.debug("Sleep 1 sec")
        time.sleep(1)
    
        # Flush buffer
        logger.debug("Serialport flush output")
        serial_param.port.flushOutput()
        logger.debug("Serialport flush input")
        serial_param.port.flushInput()

        # Send STATUS
        logger.debug("Send rfxcmd_status (" + rfxcmd.status + ")")
        serial_param.port.write( rfxcmd.status.decode('hex') )
        logger.debug("Sleep 1 sec")
        time.sleep(1)
        
        # If active (autostart)
        if config.protocol_startup:
            logger.debug("Protocol AutoStart activated")
            try:
                pMessage = protocol.set_protocolfile(config.protocol_file)
                logger.debug("Send set protocol message (" + pMessage + ")")
                serial_param.port.write( pMessage.decode('hex') )
                logger.debug("Sleep 1 sec")
                time.sleep(1)
            except Exception as err:
                logger.error("Could not create protocol message")
                pass
        
    try:
        while 1:
            # Let it breath
            # Without this sleep it will cause 100% CPU in windows
            time.sleep(0.01)
            
            if config.serial_active:
                # Read serial port
                if config.process_rfxmsg == True:
                    rawcmd = read_rfx()
                    if rawcmd:
                        logger.debug("Processed: " + str(rawcmd))
            
            # Read socket
            if config.socketserver:
                read_socket()
            
    except KeyboardInterrupt:
        logger.debug("Received keyboard interrupt")
        logger.debug("Close server socket")
        serversocket.netAdapter.shutdown()
        
        if config.serial_active:
            logger.debug("Close serial port")
            close_serialport()
        
        logger.info("\nExit...")
        pass

# ----------------------------------------------------------------------------

def option_getstatus():
    """
    Get status from RFXtrx device and logger.info(on screen)
    """
    
    # Flush buffer
    serial_param.port.flushOutput()
    serial_param.port.flushInput()

    # Send RESET
    serial_param.port.write(rfxcmd.reset.decode('hex'))
    time.sleep(1)

    # Flush buffer
    serial_param.port.flushOutput()
    serial_param.port.flushInput()

    # Send STATUS
    send_rfx(rfxcmd.status.decode('hex'))
    time.sleep(1)
    read_rfx()

# ----------------------------------------------------------------------------

def option_send():
    """
    Send command to RFX device
    
    """
    
    logger.debug("Send message to RFX device")

    # Open serial port
    logger.debug("Open serial port")
    open_serialport()

    # Remove any whitespaces    
    cmdarg.rawcmd = cmdarg.rawcmd.replace(' ', '')
    logger.debug("Message: " + cmdarg.rawcmd)

    # Test the string if it is hex format
    try:
        int(cmdarg.rawcmd,16)
    except ValueError:
        logger.error("Error: invalid rawcmd, not hex format")
        sys.exit(1)     
    
    # Check that first byte is not 00
    if ByteToHex(cmdarg.rawcmd.decode('hex')[0]) == "00":
        logger.error("Error: invalid rawcmd, first byte is zero")
        sys.exit(1)
    
    # Check if string is the length that it reports to be
    cmd_len = int( ByteToHex(cmdarg.rawcmd.decode('hex')[0]),16 )
    if not len(cmdarg.rawcmd.decode('hex')) == (cmd_len + 1):
        logger.error("Error: invalid rawcmd, invalid length")
        sys.exit(1)

    # Flush buffer
    logger.debug("Serialport flush output")
    serial_param.port.flushOutput()
    logger.debug("Serialport flush input")
    serial_param.port.flushInput()

    # Send RESET
    logger.debug("Send RFX reset")
    serial_param.port.write( rfxcmd.reset.decode('hex') )
    time.sleep(1)

    # Flush buffer
    logger.debug("Serialport flush output")
    serial_param.port.flushOutput()
    logger.debug("Serialport flush input")
    serial_param.port.flushInput()

    if cmdarg.rawcmd:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        if cmdarg.printout_complete == True:
            logger.info("------------------------------------------------")
            logger.info("Send\t\t\t= " + ByteToHex( cmdarg.rawcmd.decode('hex') ))
            logger.info("Date/Time\t\t= " + timestamp)
            logger.info("Packet Length\t\t= " + ByteToHex( cmdarg.rawcmd.decode('hex')[0] ))
            try:
                decodePacket( cmdarg.rawcmd.decode('hex') )
            except KeyError:
                logger.error("Error: unrecognizable packet")

        logger.debug("Send message")
        serial_param.port.write( cmdarg.rawcmd.decode('hex') )
        time.sleep(1)
        logger.debug("Read response")
        read_rfx()

    logger.debug("Close serial port")
    close_serialport()

# ----------------------------------------------------------------------------

def option_bsend():
    """
    Send command when rfxcmd is running
    Input: none
    
    NOTE! Will be depricated in v0.3 and removed in v0.31
    
    """
    
    logger.info("BSEND action is DEPRICATED, will be removed really soon...")
    
    logger.debug('Action: bsend')
    
    # Remove any whitespaces
    cmdarg.rawcmd = cmdarg.rawcmd.replace(' ', '')
    logger.debug('rawcmd: ' + cmdarg.rawcmd)
    
    # Test the string if it is hex format
    try:
        int(cmdarg.rawcmd,16)
    except ValueError:
        logger.error("Error: invalid rawcmd, not hex format")
        sys.exit(1)     
    
    # Check that first byte is not 00
    if ByteToHex(cmdarg.rawcmd.decode('hex')[0]) == "00":
        logger.error("Error: invalid rawcmd, first byte is zero")
        sys.exit(1)
    
    # Check if string is the length that it reports to be
    cmd_len = int( ByteToHex( cmdarg.rawcmd.decode('hex')[0]),16 )
    if not len(cmdarg.rawcmd.decode('hex')) == (cmd_len + 1):
        logger.error("Error: invalid rawcmd, invalid length")
        sys.exit(1)

    if cmdarg.rawcmd:
        serial_param.port.write(cmdarg.rawcmd.decode('hex'))

# ----------------------------------------------------------------------------

def read_configfile():
    """
    Read items from the configuration file
    """
    if os.path.exists( cmdarg.configfile ):

        # ----------------------
        # Serial device
        if (read_config(cmdarg.configfile, "serial_active") == "yes"):
            config.serial_active = True
        else:
            config.serial_active = False
        config.serial_device = read_config( cmdarg.configfile, "serial_device")
        config.serial_rate = read_config( cmdarg.configfile, "serial_rate")
        config.serial_timeout = read_config( cmdarg.configfile, "serial_timeout")

        logger.debug("Serial device: " + str(config.serial_device))
        logger.debug("Serial rate: " + str(config.serial_rate))
        logger.debug("Serial timeout: " + str(config.serial_timeout))

        # ----------------------
        # Process
        if (read_config(cmdarg.configfile, "process_rfxmsg") == "yes"):
            config.process_rfxmsg = True
        else:
            config.process_rfxmsg = False
        logger.debug("Process RFXmsg: " + str(config.process_rfxmsg))
        
        # ----------------------
        # MySQL
        if (read_config(cmdarg.configfile, "mysql_active") == "yes"):
            config.mysql_active = True
        else:
            config.mysql_active = False
        config.mysql_server = read_config( cmdarg.configfile, "mysql_server")
        config.mysql_database = read_config( cmdarg.configfile, "mysql_database")
        config.mysql_username = read_config( cmdarg.configfile, "mysql_username")
        config.mysql_password = read_config( cmdarg.configfile, "mysql_password")
    
        # ----------------------
        # TRIGGER
        if (read_config( cmdarg.configfile, "trigger_active") == "yes"):
            config.trigger_active = True
        else:
            config.trigger_active = False

        if (read_config( cmdarg.configfile, "trigger_onematch") == "yes"):
            config.trigger_onematch = True
        else:
            config.trigger_onematch = False

        config.trigger_file = read_config( cmdarg.configfile, "trigger_file")
        config.trigger_timeout = read_config( cmdarg.configfile, "trigger_timeout")

        # ----------------------
        # SQLITE
        if (read_config(cmdarg.configfile, "sqlite_active") == "yes"):
            config.sqlite_active = True
        else:
            config.sqlite_active = False        
        config.sqlite_database = read_config(cmdarg.configfile, "sqlite_database")
        config.sqlite_table = read_config(cmdarg.configfile, "sqlite_table")

        # ----------------------
        # PGSQL
        if (read_config(cmdarg.configfile, "pgsql_active") == "yes"):
            config.pgsql_active = True
        else:
            config.pgsql_active = False
        config.pgsql_server = read_config(cmdarg.configfile, "pgsql_server")
        config.pgsql_database = read_config(cmdarg.configfile, "pgsql_database")
        config.pgsql_port = read_config(cmdarg.configfile, "pgsql_port")
        config.pgsql_username = read_config(cmdarg.configfile, "pgsql_username")
        config.pgsql_password = read_config(cmdarg.configfile, "pgsql_password")
        config.pgsql_table = read_config(cmdarg.configfile, "pgsql_table")

        # ----------------------
        # GRAPHITE
        if (read_config(cmdarg.configfile, "graphite_active") == "yes"):
            config.graphite_active = True
        else:
            config.graphite_active = False
        config.graphite_server = read_config(cmdarg.configfile, "graphite_server")
        config.graphite_port = read_config(cmdarg.configfile, "graphite_port")

        # ----------------------
        # XPL
        if (read_config(cmdarg.configfile, "xpl_active") == "yes"):
            config.xpl_active = True
            config.xpl_host = read_config(cmdarg.configfile, "xpl_host")
            config.xpl_sourcename = read_config(cmdarg.configfile, "xpl_sourcename")
            if (read_config(cmdarg.configfile, "xpl_includehostname") == "yes"):
                config.xpl_includehostname = True
            else:
                config.xpl_includehostname = False
        else:
            config.xpl_active = False

        # ----------------------
        # SOCKET SERVER
        if (read_config(cmdarg.configfile, "socketserver") == "yes"):
            config.socketserver = True
        else:
            config.socketserver = False
        config.sockethost = read_config( cmdarg.configfile, "sockethost")
        config.socketport = read_config( cmdarg.configfile, "socketport")
        logger.debug("SocketServer: " + str(config.socketserver))
        logger.debug("SocketHost: " + str(config.sockethost))
        logger.debug("SocketPort: " + str(config.socketport))
        
        # -----------------------
        # WHITELIST
        if (read_config(cmdarg.configfile, "whitelist_active") == "yes"):
            config.whitelist_active = True
        else:
            config.whitelist_active = False         
        config.whitelist_file = read_config( cmdarg.configfile, "whitelist_file")
        logger.debug("Whitelist_active: " + str(config.whitelist_active))
        logger.debug("Whitelist_file: " + str(config.whitelist_file))

        # -----------------------
        # DAEMON
        if (read_config(cmdarg.configfile, "daemon_active") == "yes"):
            config.daemon_active = True
        else:
            config.daemon_active = False
        config.daemon_pidfile = read_config( cmdarg.configfile, "daemon_pidfile")
        logger.debug("Daemon_active: " + str(config.daemon_active))
        logger.debug("Daemon_pidfile: " + str(config.daemon_pidfile))
        
        # -----------------------
        # WEEWX
        if (read_config(cmdarg.configfile, "weewx_active") == "yes"):
            config.weewx_active = True
        else:
            config.weewx_active = False
        config.weewx_config = read_config( cmdarg.configfile, "weewx_config")
        logger.debug("WeeWx_active: " + str(config.weewx_active))
        logger.debug("WeeWx_config: " + str(config.weewx_config))
        
        # ------------------------
        # RRD
        if (read_config(cmdarg.configfile, "rrd_active") == "yes"):
            config.rrd_active = True
        else:
            config.rrd_active = False
        
        # If RRD path is empty, then use the script path
        config.rrd_path = read_config( cmdarg.configfile, "rrd_path")
        if not config.rrd_path:
            config.rrd_path = os.path.dirname(os.path.realpath(__file__))
        
        # ------------------------
        # BAROMETRIC
        config.barometric = read_config(cmdarg.configfile, "barometric")
        
        # ------------------------
        # LOG MESSAGES
        if (read_config(cmdarg.configfile, "log_msg") == "yes"):
            config.log_msg = True
        else:
            config.log_msg = False
        config.log_msgfile = read_config(cmdarg.configfile, "log_msgfile")
        
        # ------------------------
        # PROTOCOLS
        if (read_config(cmdarg.configfile, "protocol_startup") == "yes"):
            config.protocol_startup = True
        else:
            config.protocol_startup = False
        config.protocol_file = read_config(cmdarg.configfile, "protocol_file")
        
    else:
        # config file not found, set default values
        logger.error("Error: Configuration file not found (" + cmdarg.configfile + ")")
        logger.error("Error: Configuration file not found (" + cmdarg.configfile + ") Line: " + _line())

# ----------------------------------------------------------------------------

def open_serialport():
    """
    Open serial port for communication to the RFXtrx device.
    """

    # Check that serial module is loaded
    try:
        logger.debug("Serial extension version: " + serial.VERSION)
    except:
        logger.error("Error: You need to install Serial extension for Python")
        logger.error("Error: Serial extension for Python could not be loaded")
        logger.debug("Exit 1")
        sys.exit(1)

    # Check for serial device
    if config.device:
        logger.debug("Device: " + config.device)
    else:
        logger.error("Device name missing. Line: " + _line())
        logger.info("Serial device is missing")
        logger.debug("Exit 1")
        sys.exit(1)

    # Open serial port
    logger.debug("Open Serialport")
    try:  
        serial_param.port = serial.Serial(config.device, serial_param.rate, timeout=serial_param.timeout)
    except serial.SerialException, e:
        logger.error("Error: Failed to connect on device " + config.device + " Line: " + _line())
        logger.error("Error: Failed to connect on device " + config.device)
        logger.error("Error: " + str(e))
        logger.debug("Exit 1")
        sys.exit(1)

    if not serial_param.port.isOpen():
        serial_param.port.open()

# ----------------------------------------------------------------------------

def close_serialport():
    """
    Close serial port.
    """

    logger.debug("Close serial port")
    try:
        serial_param.port.close()
        logger.debug("Serial port closed")
    except:
        logger.error("Failed to close the serial port (" + device + ") Line: " + _line())
        logger.error("Error: Failed to close the port " + device)
        logger.debug("Exit 1")
        sys.exit(1)

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
    
    if os.path.exists( os.path.join(program_path, configfile) ):
        
        # Read config file
        f = open(os.path.join(program_path, configfile),'r')
        data = f.read()
        f.close()
        
        try:
            dom = minidom.parseString(data)
        except:
            logger.error("Error: problem in the %s file, cannot process it" % str(configfile))
            return False
        
        if dom:
            
            #formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
            formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(module)s:%(lineno)d - %(levelname)s - %(message)s')
            
            # Get loglevel from config file
            try:
                xmlTag = dom.getElementsByTagName( 'loglevel' )[0].toxml()
                loglevel = xmlTag.replace('<loglevel>','').replace('</loglevel>','')
                loglevel = loglevel.upper()
            except:
                loglevel = "ERROR"
            
            # Get logfile from config file
            try:
                xmlTag = dom.getElementsByTagName( 'logfile' )[0].toxml()
                logfile = xmlTag.replace('<logfile>','').replace('</logfile>','')
            except:
                logfile = None
                pass
            
            if debug:
                loglevel = "DEBUG"
                handler = logging.StreamHandler()
                handler.setFormatter(formatter)
                logger = logging.getLogger(name)
                logger.setLevel(logging.getLevelName(loglevel))
                logger.addHandler(handler)
            
            if logfile:
                handler = logging.FileHandler(logfile)
                handler.setFormatter(formatter)
                logger = logging.getLogger(name)
                logger.setLevel(logging.getLevelName(loglevel))
                logger.addHandler(handler)
            
            return logger
        
    else:
        logger.error("Error: Cannot find configuration file (%s)" % str(configfile))
        return False
    
# ----------------------------------------------------------------------------

def main():

    global logger

    # Get directory of the rfxcmd script
    config.program_path = os.path.dirname(os.path.realpath(__file__))

    parser = OptionParser()
    parser.add_option("-d", "--device", action="store", type="string", dest="device", help="The serial device of the RFXCOM, example /dev/ttyUSB0")
    parser.add_option("-l", "--listen", action="store_true", dest="listen", help="Listen for messages from RFX device")
    parser.add_option("-x", "--simulate", action="store", type="string", dest="simulate", help="Simulate one incoming data message")
    parser.add_option("-s", "--sendmsg", action="store", type="string", dest="sendmsg", help="Send one message to RFX device")
    parser.add_option("-f", "--rfxstatus", action="store_true", dest="rfxstatus", help="Get RFX device status")
    parser.add_option("-o", "--config", action="store", type="string", dest="config", help="Specify the configuration file")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Output all messages to stdout")
    parser.add_option("-c", "--csv", action="store_true", dest="csv", default=False, help="Output all messages to stdout in CSV format")
    parser.add_option("-V", "--version", action="store_true", dest="version", help="Print rfxcmd version information")
    parser.add_option("-D", "--debug", action="store_true", dest="debug", default=False, help="Debug printout on stdout")
    parser.add_option("--listprotocol", action="store_true", dest="listprotocol", default=False, help="List protocol settings")
    (options, args) = parser.parse_args()

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
    if options.debug:
        logger = logger_init(cmdarg.configfile,'rfxcmd', True)
    else:
        logger = logger_init(cmdarg.configfile,'rfxcmd', False)
    
    if not logger:
        logger.error("Error: Cannot find configuration file (%s)" % str(configfile))
        sys.exit(1)
    
    logger.debug("Python version: %s.%s.%s" % sys.version_info[:3])
    logger.debug("RFXCMD Version: " + __version__)
    logger.debug(__date__.replace('$', ''))
    
    # ----------------------------------------------------------
    # PROCESS CONFIG.XML
    logger.debug("Configfile: " + cmdarg.configfile)
    logger.debug("Read configuration file")
    read_configfile()

    # ----------------------------------------------------------
    # VERBOSE OUTPUT
    if options.verbose:
        logger.debug("Verbose printout " + _line())
        cmdarg.printout_complete = True
        logger.info("RFXCMD Version " + __version__)
    else:
        cmdarg.printout_complete = False

    # ----------------------------------------------------------
    # CSV OUTPUT
    if options.csv:
        logger.debug("CSV printout")
        cmdarg.printout_csv = True
    else:
        cmdarg.printout_csv = False
    
    # ----------------------------------------------------------
    # Print protocol list
    if options.listprotocol:
        logger.debug("List protocol file to screen")
        protocol.print_protocolfile(config.protocol_file)
    
    # ----------------------------------------------------------
    # WHITELIST
    if config.whitelist_active:
        logger.debug("Read whitelist file")
        read_whitelistfile()

    # ----------------------------------------------------------
    # Triggerlist
    if config.trigger_active:
        logger.debug("Read triggerlist file")
        read_triggerfile()

    # ----------------------------------------------------------
    # WEEWXLIST
    if config.weewx_active:
        logger.debug("Read WeeWxlist file")
        read_weewxfile()

    # ----------------------------------------------------------
    # MYSQL
    if config.mysql_active:
        logger.debug("MySQL active, Check MySQL")
        try:
            import MySQLdb
        except ImportError:
            logger.error("Error: You need to install MySQL extension for Python")
            logger.error("Error: Could not find MySQL extension for Python. Line: " + _line())
            logger.debug("Exit 1")
            sys.exit(1)     

    # ----------------------------------------------------------
    # SQLITE
    if config.sqlite_active:
        logger.debug("SqLite active, Check sqlite3 version")
        try:
            logger.debug("SQLite3 version: " + sqlite3.sqlite_version)
        except ImportError:
            logger.error("Error: You need to install SQLite extension for Python")
            logger.error("Error: Could not find MySQL extension for Python. " + _line())
            logger.debug("Exit 1")
            sys.exit(1)
    
    # ----------------------------------------------------------
    # PGSQL
    if config.pgsql_active:
        logger.debug("pgSQL active, Check pgSQL")
        try:
            import psycopg2
        except ImportError:
            logger.error("Error: You need to install pg extension for Python")
            logger.error("Error: Could not find pgSQL extension for Python. Line: " + _line())
            logger.debug("Exit 1")
            sys.exit(1)

    # ----------------------------------------------------------
    # XPL
    if config.xpl_active:
        logger.debug("XPL active")

    # ----------------------------------------------------------
    # GRAPHITE
    if config.graphite_active:
        logger.debug("Graphite active")

    # ----------------------------------------------------------
    # RRD
    if config.rrd_active:
        logger.debug("RRD active")

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
        logger.debug("Daemon")
        logger.debug("Check PID file")
        
        if config.daemon_pidfile:
            cmdarg.pidfile = config.daemon_pidfile
            cmdarg.createpid = True
            logger.debug("PID file '" + cmdarg.pidfile + "'")
        
            if os.path.exists(cmdarg.pidfile):
                logger.info("PID file '" + cmdarg.pidfile + "' already exists. Exiting.")
                logger.debug("PID file '" + cmdarg.pidfile + "' already exists.")
                logger.debug("Exit 1")
                sys.exit(1)
            else:
                logger.debug("PID file does not exists")

        else:
            logger.info("You need to set the --pidfile parameter at the startup")
            logger.error("Command argument --pidfile missing. Line: " + _line())
            logger.debug("Exit 1")
            sys.exit(1)

        logger.debug("Check platform")
        if sys.platform == 'win32':
            logger.info("Daemonize not supported under Windows. Exiting.")
            logger.error("Daemonize not supported under Windows. Line: " + _line())
            logger.debug("Exit 1")
            sys.exit(1)
        else:
            logger.debug("Platform: " + sys.platform)
            
            try:
                logger.debug("Write PID file")
                file(cmdarg.pidfile, 'w').write("pid\n")
            except IOError, e:
                logger.error("Line: " + _line())
                logger.error("Unable to write PID file: %s [%d]" % (e.strerror, e.errno))
                raise SystemExit("Unable to write PID file: %s [%d]" % (e.strerror, e.errno))

            logger.debug("Deactivate screen printouts")
            cmdarg.printout_complete = False

            logger.debug("Start daemon")
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
    
    logger.debug("Exit 0")
    sys.exit(0)
    
# ------------------------------------------------------------------------------

if __name__ == '__main__':

    # Init shutdown handler
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    # Init objects
    config = config_data()
    cmdarg = cmdarg_data()
    rfx = lib.rfx_sensors.rfx_data()
    rfxcmd = rfxcmd_data()
    serial_param = serial_data()
    
    # Triggerlist
    triggerlist = trigger_data()
    
    # Whitelist
    whitelist = whitelist_data()

    # WeeWxlist
    weewxlist = weewx_data()

    # Check python version
    check_pythonversion()
    
    main()

# ------------------------------------------------------------------------------
# END
# ------------------------------------------------------------------------------
