#!/usr/bin/env python3
# coding=UTF-8
"""
Decoding 0x3. protocols
"""

__author__ = "Sebastian Sjoholm"
__copyright__ = "Copyright 2012-2014, Sebastian Sjoholm"
__license__ = "GPL"
__version__ = "2.0.0"
__maintainer__ = "Nicolas Béguier"
__date__ = "$Date: 2019-06-12 08:05:33 +0100 (Thu, 12 Jun 2019) $"

# RFXCMD library
import lib.rfx_sensors
from lib.rfx_utils import ByteToHex
import lib.rfx_decode as rfxdecode

RFX = lib.rfx_sensors.rfx_data()

def decode_0x30(message, subtype, seqnbr, id1):
    """
    0x30 Remote control and IR
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_30[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    command_hex = ByteToHex(message[5])
    cmndtype_hex = ByteToHex(message[7])
    command = None
    cmndtype = None
    toggle = None
    if subtype == '00':
        try:
            command = RFX.rfx_subtype_30_atiremotewonder[command_hex]
        except KeyError:
            command = '0x' + command_hex
    elif subtype == '02':
        command = RFX.rfx_subtype_30_medion[command_hex]
    elif subtype == '04':
        if cmndtype_hex == '00':
            cmndtype = "PC"
        elif cmndtype_hex == '01':
            cmndtype = "AUX1"
        elif cmndtype_hex == '02':
            cmndtype = "AUX2"
        elif cmndtype_hex == '03':
            cmndtype = "AUX3"
        elif cmndtype_hex == '04':
            cmndtype = "AUX4"
        else:
            cmndtype = "Unknown"
        result.append({'key': 'Command type', 'value': cmndtype})
        toggle = ByteToHex(message[6])
        result.append({'key': 'Toggle', 'value': toggle})

    result.append({'key': 'Command', 'value': command})

    result.append({'key': 'Id', 'value': id1})

    signal = rfxdecode.decode_signal(message[6])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('signal_level', signal),
        ('id', id1),
        ('toggle', toggle),
        ('cmndtype', cmndtype),
        ('command', command)]

    return result, output_extra
