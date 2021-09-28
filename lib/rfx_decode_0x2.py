#!/usr/bin/env python3
# coding=UTF-8
"""
Decoding 0x2. protocols
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

def decode_0x20(message, subtype, seqnbr, id1, id2):
    """
    0x20 Security1
    Credit: Dimitri Clatot
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_20[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2 + ByteToHex(message[6])
    result.append({'key': 'Id', 'value': sensor_id})

    try:
        status = RFX.rfx_subtype_20_status[ByteToHex(message[7])]
    except KeyError:
        status = '0x' + ByteToHex(message[7])
    result.append({'key': 'Status', 'value': status})

    battery = rfxdecode.decode_battery(message[8])
    result.append({'key': 'Battery', 'value': battery})

    signal = rfxdecode.decode_signal(message[8])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('battery', battery),
        ('signal_level', signal),
        ('id', sensor_id),
        ('status', status)]

    return result, output_extra


def decode_0x28(subtype, seqnbr):
    """
    0x28 Camera1
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_28[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    return result, []
