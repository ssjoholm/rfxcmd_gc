#!/usr/bin/env python3
# coding=UTF-8

# ------------------------------------------------------------------------------
#
#    RFX_UTILS.PY
#
#    Copyright (C) 2012-2013 Sebastian Sjoholm, sebastian.sjoholm@gmail.com
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
#    Version history can be found at
#    http://code.google.com/p/rfxcmd/wiki/VersionHistory
#
#    $Rev: 464 $
#    $Date: 2013-05-01 22:41:36 +0200 (Wed, 01 May 2013) $
#
# ------------------------------------------------------------------------------

__author__ = "Sebastian Sjoholm"
__copyright__ = "Copyright 2012-2014, Sebastian Sjoholm"
__license__ = "GPL"
__version__ = "2.0.0"
__maintainer__ = "Nicolas Béguier"
__date__ = "$Date: 2019-06-12 08:05:33 +0100 (Thu, 12 Jun 2019) $"

from lib.rfx_utils import ByteToHex, clearBit, testBit

# ----------------------------------------------------------------------------

def decode_temperature(message_high, message_low):
    """
    Decode temperature bytes.
    """
    temp_high = ByteToHex(message_high)
    temp_low = ByteToHex(message_low)
    polarity = testBit(int(temp_high, 16), 7)

    if polarity == 128:
        polarity_sign = "-"
    else:
        polarity_sign = ""

    temp_high = clearBit(int(temp_high, 16), 7)
    temp_high = temp_high << 8
    temperature = (temp_high + int(temp_low, 16)) * 0.1
    temperature_str = polarity_sign + str(temperature)

    return temperature_str

# ----------------------------------------------------------------------------

def decode_signal(message):
    """
    Decode signal byte.
    """
    signal = int(ByteToHex(message), 16) >> 4
    return signal

# ----------------------------------------------------------------------------

def decode_battery(message):
    """
    Decode battery byte.
    """
    battery = int(ByteToHex(message), 16) & 0xf
    return battery

# ----------------------------------------------------------------------------

def decode_power(message_1, message_2, message_3):
    """
    Decode power bytes.
    """
    power_1 = ByteToHex(message_1)
    power_2 = ByteToHex(message_2)
    power_3 = ByteToHex(message_3)

    power_1 = int(power_1, 16)
    power_1 = power_1 << 16
    power_2 = int(power_2, 16) << 8
    power_3 = int(power_3, 16)
    power = (power_1 + power_2 + power_3)
    power_str = str(power)

    return power_str

# ----------------------------------------------------------------------------
