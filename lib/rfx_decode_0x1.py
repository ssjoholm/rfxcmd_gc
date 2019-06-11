#!/usr/bin/env python3
# coding=UTF-8
"""
Decoding 0x1. protocols
"""

__author__ = "Sebastian Sjoholm"
__copyright__ = "Copyright 2012-2014, Sebastian Sjoholm"
__license__ = "GPL"
__version__ = "2.0.0"
__maintainer__ = "Nicolas Béguier"
__date__ = "$Date: 2019-06-12 08:05:33 +0100 (Thu, 12 Jun 2019) $"

# RFXCMD library
import lib.rfx_sensors
from lib.rfx_utils import ByteToHex, dec2bin, testBit
import lib.rfx_decode as rfxdecode

RFX = lib.rfx_sensors.rfx_data()

def decode_0x10(message, subtype, seqnbr):
    """
    0x10 Lighting1
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_10[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = ByteToHex(message[4]) + ByteToHex(message[5]) + \
        ByteToHex(message[6]) + ByteToHex(message[7])
    result.append({'key': 'Id', 'value': sensor_id})

    try:
        housecode = RFX.rfx_subtype_10_housecode[ByteToHex(message[4])]
    except KeyError:
        housecode = '0x' + ByteToHex(message[4])
    result.append({'key': 'Housecode', 'value': housecode})

    unitcode = int(ByteToHex(message[5]), 16)
    result.append({'key': 'Unitcode', 'value': unitcode})

    try:
        command = RFX.rfx_subtype_10_cmnd[ByteToHex(message[6])]
    except KeyError:
        command = '0x' + ByteToHex(message[6])
    result.append({'key': 'Command', 'value': command})

    signal = rfxdecode.decode_signal(message[7])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('signal_level', signal),
        ('housecode', housecode),
        ('command', command),
        ('unitcode', unitcode)]

    return result, output_extra

def decode_0x11(message, subtype, seqnbr):
    """
    0x11 Lighting2
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_11[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = ByteToHex(message[4]) + ByteToHex(message[5]) + \
        ByteToHex(message[6]) + ByteToHex(message[7])
    result.append({'key': 'Id', 'value': sensor_id})

    unitcode = int(ByteToHex(message[8]), 16)
    result.append({'key': 'Unitcode', 'value': unitcode})

    try:
        command = RFX.rfx_subtype_11_cmnd[ByteToHex(message[9])]
    except KeyError:
        command = '0x' + ByteToHex(message[9])
    result.append({'key': 'Command', 'value': command})

    try:
        dimlevel = RFX.rfx_subtype_11_dimlevel[ByteToHex(message[10])]
    except KeyError:
        dimlevel = '0x' + ByteToHex(message[10])
    result.append({'key': 'Dim level', 'value': dimlevel, 'unit': '%'})

    signal = rfxdecode.decode_signal(message[11])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('signal_level', signal),
        ('id', sensor_id),
        ('command', command),
        ('unitcode', unitcode),
        ('dim_level', dimlevel)]

    return result, output_extra


def decode_0x12(message, subtype, seqnbr):
    """
    0x12 Lighting3
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_12[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    system = ByteToHex(message[4])
    result.append({'System': 'Command', 'value': system})

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
    result.append({'key': 'Channel', 'value': channel})

    try:
        command = RFX.rfx_subtype_12_cmnd[ByteToHex(message[7])]
    except KeyError:
        command = '0x' + ByteToHex(message[7])
    result.append({'key': 'Command', 'value': command})

    battery = rfxdecode.decode_battery(message[8])
    result.append({'key': 'Battery', 'value': battery})

    signal = rfxdecode.decode_signal(message[8])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('battery', battery),
        ('signal', signal),
        ('system', system),
        ('command', command),
        ('channel', channel)]

    return result, output_extra


def decode_0x13(message, subtype, seqnbr):
    """
    0x13 Lighting4
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_13[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    code = ByteToHex(message[4]) + ByteToHex(message[5]) + ByteToHex(message[6])
    result.append({'key': 'Code', 'value': code})

    code1 = dec2bin(int(ByteToHex(message[4]), 16))
    code2 = dec2bin(int(ByteToHex(message[5]), 16))
    code3 = dec2bin(int(ByteToHex(message[6]), 16))
    code_bin = code1 + " " + code2 + " " + code3
    result.append({'key': 'S1-S24', 'value': code_bin})

    pulse = ((int(ByteToHex(message[7]), 16) * 256) + int(ByteToHex(message[8]), 16))
    result.append({'key': 'Code', 'value': pulse, 'unit': 'usec'})

    signal = rfxdecode.decode_signal(message[9])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('code', code),
        ('s1_s24', code_bin),
        ('pulse', pulse),
        ('signal', signal)]

    return result, output_extra

def decode_0x14(message, subtype, seqnbr, id1, id2):
    """
    0x14 Lighting5
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_14[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2 + ByteToHex(message[6])
    result.append({'key': 'Id', 'value': sensor_id})

    command_hex = ByteToHex(message[8])
    level = 0
    unitcode = 'Not used'
    try:
        if subtype == '00':
            command = RFX.rfx_subtype_14_cmnd0[command_hex]
            unitcode = int(ByteToHex(message[7]), 16)
            level = ByteToHex(message[9])
        elif subtype == '01':
            command = RFX.rfx_subtype_14_cmnd1[command_hex]
            unitcode = int(ByteToHex(message[7]), 16)
        elif subtype == '02':
            command = RFX.rfx_subtype_14_cmnd2[command_hex]
            unitcode = int(ByteToHex(message[7]), 16)
        elif subtype == '03':
            command = RFX.rfx_subtype_14_cmnd3[command_hex]
        elif subtype == '04':
            command = RFX.rfx_subtype_14_cmnd4[command_hex]
            unitcode = int(ByteToHex(message[7]), 16)
        elif subtype == '05':
            command = RFX.rfx_subtype_14_cmnd5[command_hex]
        elif subtype == '06':
            unitcode = int(ByteToHex(message[7]), 16)
            try:
                command = RFX.rfx_subtype_14_cmnd5[command_hex]
            except KeyError:
                # if the value is between x06 and x84 it is 'select color'
                # This should be improved, as it will not catch unknown values
                command = 'Select Color'
        elif subtype == '11':
            unitcode = int(ByteToHex(message[7]), 16)
            command = RFX.rfx_subtype_14_cmnd11[command_hex]
        else:
            command = '0x' + command_hex
    except KeyError:
        command = '0x' + command_hex
    result.append({'key': 'Command', 'value': command})
    result.append({'key': 'Level', 'value': level})
    result.append({'key': 'Unitcode', 'value': unitcode})

    signal = rfxdecode.decode_signal(message[10])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('id', sensor_id),
        ('unitcode', unitcode),
        ('command', command),
        ('level', level),
        ('signal_level', signal)]

    return result, output_extra

def decode_0x15(message, subtype, seqnbr, id1, id2):
    """
    0x15 Lighting6
    Credit: Dimitri Clatot
   """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_15[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    try:
        groupcode = RFX.rfx_subtype_15_groupcode[ByteToHex(message[6])]
    except KeyError:
        groupcode = '0x' + ByteToHex(message[6])
    result.append({'key': 'Groupcode', 'value': groupcode})

    unitcode = int(ByteToHex(message[7]), 16)
    result.append({'key': 'Unitcode', 'value': unitcode})

    try:
        command = RFX.rfx_subtype_15_cmnd[ByteToHex(message[8])]
    except KeyError:
        command = '0x' + ByteToHex(message[8])
    result.append({'key': 'Command', 'value': command})

    command_seqnbr = ByteToHex(message[9])
    result.append({'key': 'Command seqnbr', 'value': command_seqnbr})

    seqnbr2 = ByteToHex(message[10])
    result.append({'key': 'Seqnbr2', 'value': seqnbr2})

    signal = rfxdecode.decode_signal(message[11])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('id', sensor_id),
        ('signal_level', signal),
        ('groupcode', groupcode),
        ('command', command),
        ('unitcode', unitcode),
        ('seqnbr', seqnbr2),
        ('command_seqnbr', command_seqnbr)]

    return result, output_extra


def decode_0x16(message, subtype, seqnbr, id1, id2):
    """
    0x16 Chime
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_16[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    if subtype == '00':
        try:
            sound = RFX.rfx_subtype_16_sound[ByteToHex(message[6])]
        except KeyError:
            sound = '0x' + ByteToHex(message[6])
    elif subtype == '02' or subtype == '03' or subtype == '04':
        sound = None
    else:
        sound = '0x' + ByteToHex(message[6])
    result.append({'key': 'Sound', 'value': sound})

    signal = rfxdecode.decode_signal(message[7])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('id', sensor_id),
        ('sound', sound),
        ('signal_level', signal)]

    return result, output_extra


def decode_0x17(subtype, seqnbr):
    """
    0x17 Fan (Transmitter only)
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_17[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    return result, []


def decode_0x18(subtype, seqnbr):
    """
    0x18 Curtain1 (Transmitter only)
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_18[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    return result, []


def decode_0x19(subtype, seqnbr):
    """
    0x19 Blinds1
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_19[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    return result, []


def decode_0x1a(message, subtype, seqnbr, id1, id2):
    """
    0x11 RTS
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_1A[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2 + ByteToHex(message[6])
    result.append({'key': 'Id1-3', 'value': sensor_id})

    if subtype == '00' and ByteToHex(message[6]) == '00':
        unitcode = 'All'
    else:
        unitcode = '0x' + ByteToHex(message[6])
    result.append({'key': 'Unitcode', 'value': unitcode})

    try:
        command = RFX.rfx_subtype_1A_cmnd[ByteToHex(message[7])]
    except KeyError:
        command = '0x' + ByteToHex(message[7])
    result.append({'key': 'Command', 'value': command})

    signal = rfxdecode.decode_signal(message[8])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('signal_level', signal),
        ('id', sensor_id),
        ('unicode', unitcode),
        ('command', command)]

    return result, output_extra
