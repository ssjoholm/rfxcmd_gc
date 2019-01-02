#!/usr/bin/python
# coding=UTF-8
"""
Decoding 0x5. protocols
"""

# RFXCMD library
import lib.rfx_sensors
from lib.rfx_utils import ByteToHex, clearBit
import lib.rfx_decode as rfxdecode

RFX = lib.rfx_sensors.rfx_data()

def decode_0x50(message, subtype, seqnbr, id1, id2):
    """
    0x50 - Temperature sensors
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_50[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    temperature = rfxdecode.decode_temperature(message[6], message[7])
    result.append({'key': 'Temperature', 'value': temperature, 'unit': 'C'})

    signal = rfxdecode.decode_signal(message[8])
    result.append({'key': 'Signal level', 'value': signal})

    battery = rfxdecode.decode_battery(message[8])
    result.append({'key': 'Battery', 'value': battery})

    output_extra = [
        ('id', sensor_id),
        ('battery', battery),
        ('signal_level', signal),
        ('temperature', temperature)]

    return result, output_extra


def decode_0x51(message, subtype, seqnbr, id1, id2):
    """
    0x51 Humidity sensors
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_51[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    humidity = int(ByteToHex(message[6]), 16)
    result.append({'key': 'Humidity', 'value': humidity, 'unit': '%'})

    try:
        humidity_status = RFX.rfx_subtype_51_humstatus[ByteToHex(message[7])]
    except KeyError:
        humidity_status = '0x' + ByteToHex(message[7])
    result.append({'key': 'Humidity', 'value': humidity_status})

    signal = rfxdecode.decode_signal(message[8])
    result.append({'key': 'Signal level', 'value': signal})

    battery = rfxdecode.decode_battery(message[8])
    result.append({'key': 'Battery', 'value': battery})

    output_extra = [
        ('id', sensor_id),
        ('humidity_status', humidity_status),
        ('humidity', humidity),
        ('battery', battery),
        ('signal_level', signal)]

    return result, output_extra


def decode_0x52(message, subtype, seqnbr, id1, id2):
    """
    0x52 Temperature and humidity sensors
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_52[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    temperature = rfxdecode.decode_temperature(message[6], message[7])
    result.append({'key': 'Temperature', 'value': temperature, 'unit': 'C'})

    humidity = int(ByteToHex(message[8]), 16)
    result.append({'key': 'Humidity', 'value': humidity, 'unit': '%'})

    try:
        humidity_status = RFX.rfx_subtype_52_humstatus[ByteToHex(message[9])]
    except KeyError:
        humidity_status = '0x' + ByteToHex(message[9])
    result.append({'key': 'Humidity Status', 'value': humidity_status})

    signal = rfxdecode.decode_signal(message[10])
    result.append({'key': 'Signal level', 'value': signal})

    battery = rfxdecode.decode_battery(message[10])
    result.append({'key': 'Battery', 'value': battery})

    output_extra = [
        ('id', sensor_id),
        ('humidity_status', humidity_status),
        ('temperature', temperature),
        ('humidity', humidity),
        ('battery', battery),
        ('signal_level', signal)]

    return result, output_extra


def decode_0x53(subtype, seqnbr):
    """
    0x53 Barometric
    RESERVED FOR FUTURE
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_53[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    return result, []


def decode_0x54(message, subtype, seqnbr, id1, id2, config_barometric=0):
    """
    0x54 Temperature, humidity and barometric sensors
    Credit: Jean-Baptiste Bodart
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_54[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    temperature = rfxdecode.decode_temperature(message[6], message[7])
    result.append({'key': 'Temperature', 'value': temperature, 'unit': 'C'})

    humidity = int(ByteToHex(message[8]), 16)
    result.append({'key': 'Humidity', 'value': humidity, 'unit': '%'})

    try:
        humidity_status = RFX.rfx_subtype_54_humstatus[ByteToHex(message[9])]
    except KeyError:
        humidity_status = '0x' + ByteToHex(message[9])
    result.append({'key': 'Humidity Status', 'value': humidity_status})

    barometric_high = ByteToHex(message[10])
    barometric_low = ByteToHex(message[11])
    barometric_high = clearBit(int(barometric_high, 16), 7)
    barometric_high = barometric_high << 8
    barometric = barometric_high + int(barometric_low, 16) + int(config_barometric)
    result.append({'key': 'Barometric pressure', 'value': humidity_status, 'unit': 'hPa'})

    try:
        forecast = RFX.rfx_subtype_54_forecast[ByteToHex(message[12])]
    except KeyError:
        forecast = '0x' + ByteToHex(message[12])
    result.append({'key': 'Forecast Status', 'value': forecast})

    signal = rfxdecode.decode_signal(message[13])
    result.append({'key': 'Signal level', 'value': signal})

    battery = rfxdecode.decode_battery(message[13])
    result.append({'key': 'Battery', 'value': battery})

    output_extra = [
        ('battery', battery),
        ('signal_level', signal),
        ('id', sensor_id),
        ('forecast_status', forecast),
        ('humidity_status', humidity_status),
        ('humidity', humidity),
        ('barometric_pressure', barometric),
        ('temperature', temperature)]

    return result, output_extra

def decode_0x55(message, subtype, seqnbr, id1, id2):
    """
    0x55 Rain sensors
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_55[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    rainrate_high = ByteToHex(message[6])
    rainrate_low = ByteToHex(message[7])
    rainrate = 'not implemented'
    if subtype == '01':
        rainrate = int(rainrate_high, 16) * 0x100 + int(rainrate_low, 16)
    elif subtype == '02':
        rainrate = float(int(rainrate_high, 16) * 0x100 + int(rainrate_low, 16)) / 100
    result.append({'key': 'Rainrate', 'value': rainrate, 'unit': 'mm/h'})

    raintotal = 'not implemented'
    if subtype != '06':
        raintotal = float( \
                    (int(ByteToHex(message[8]), 16) * 0x1000) + \
                    (int(ByteToHex(message[9]), 16) * 0x100) + \
                    int(ByteToHex(message[10]), 16)) / 10
    result.append({'key': 'Rain', 'value': raintotal, 'unit': 'mm'})

    signal = rfxdecode.decode_signal(message[11])
    result.append({'key': 'Signal level', 'value': signal})

    battery = rfxdecode.decode_battery(message[11])
    result.append({'key': 'Battery', 'value': battery})

    output_extra = [
        ('rainrate', rainrate),
        ('raintotal', raintotal),
        ('battery', battery),
        ('id', sensor_id),
        ('signal_level', signal)]

    return result, output_extra


def decode_0x56(message, subtype, seqnbr, id1, id2):
    """
    0x56 Wind sensors
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_56[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    direction = ((int(ByteToHex(message[6]), 16) * 256) + \
                int(ByteToHex(message[7]), 16))
    result.append({'key': 'Wind direction', 'value': direction, 'unit': 'degrees'})

    av_speed = 'not implemented'
    if subtype != '05':
        av_speed = ((int(ByteToHex(message[8]), 16) * 256) + \
                   int(ByteToHex(message[9]), 16)) * 0.1
    result.append({'key': 'Wind speed (average)', 'value': av_speed, 'unit': 'm/s'})

    gust = ((int(ByteToHex(message[10]), 16) * 256) + \
           int(ByteToHex(message[11]), 16)) * 0.1
    result.append({'key': 'Wind gust', 'value': gust, 'unit': 'm/s'})

    temperature = 'not implemented'
    windchill = 'not implemented'
    if subtype == "04":
        temperature = rfxdecode.decode_temperature(message[12], message[13])
        windchill = rfxdecode.decode_temperature(message[14], message[15])
    result.append({'key': 'Temperature', 'value': temperature, 'unit': 'C'})
    result.append({'key': 'Wind chill', 'value': windchill, 'unit': 'C'})

    signal = rfxdecode.decode_signal(message[16])
    result.append({'key': 'Signal level', 'value': signal})

    battery = rfxdecode.decode_battery(message[16])
    result.append({'key': 'Battery', 'value': battery})

    output_extra = [
        ('battery', battery),
        ('signal_level', signal),
        ('id', sensor_id),
        ('temperature', temperature),
        ('wind_average_speed', av_speed),
        ('wind_gust', gust),
        ('wind_direction', direction),
        ('wind_chill', windchill)]

    return result, output_extra


def decode_0x57(message, subtype, seqnbr, id1, id2):
    """
    0x57 UV Sensor
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_57[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    ultra_violet = int(ByteToHex(message[6]), 16) * 10
    result.append({'key': 'Ultra Violet', 'value': ultra_violet})

    temperature = 'not implemented'
    if subtype == '03':
        temperature = rfxdecode.decode_temperature(message[6], message[8])
    result.append({'key': 'Temperature', 'value': temperature, 'unit': 'C'})

    signal = rfxdecode.decode_signal(message[9])
    result.append({'key': 'Signal level', 'value': signal})

    battery = rfxdecode.decode_battery(message[9])
    result.append({'key': 'Battery', 'value': battery})

    output_extra = [
        ('id', sensor_id),
        ('ultra_violet', ultra_violet),
        ('temperature', temperature),
        ('battery', battery),
        ('signal_level', signal)]

    return result, output_extra


def decode_0x58(message, subtype, seqnbr, id1, id2):
    """
    0x58 Date/Time sensor
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_58[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    date_yy = int(ByteToHex(message[6]), 16)
    date_mm = int(ByteToHex(message[7]), 16)
    date_dd = int(ByteToHex(message[8]), 16)
    date_string = "20%s-%s-%s" % (
        str(date_yy).zfill(2),
        str(date_mm).zfill(2),
        str(date_dd).zfill(2))
    result.append({'key': 'Date (yy-mm-dd)', 'value': date_string})

    date_dow = int(ByteToHex(message[9]), 16)
    result.append({'key': 'Day of week (1-7)', 'value': date_dow})

    time_hr = int(ByteToHex(message[10]), 16)
    time_min = int(ByteToHex(message[11]), 16)
    time_sec = int(ByteToHex(message[12]), 16)
    time_string = "%s:%s:%s" % (str(time_hr), str(time_min), str(time_sec))
    result.append({'key': 'Time', 'value': time_string})

    signal = rfxdecode.decode_signal(message[13])
    result.append({'key': 'Signal level', 'value': signal})

    battery = rfxdecode.decode_battery(message[13])
    result.append({'key': 'Battery', 'value': battery})

    output_extra = [
        ('id', sensor_id),
        ('time', time_string),
        ('date', date_string),
        ('day_of_week', date_dow),
        ('battery', battery),
        ('signal_level', signal)]

    return result, output_extra


def decode_0x59(message, subtype, seqnbr, id1, id2):
    """
    0x59 Current Sensor
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_59[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    count = int(ByteToHex(message[6]), 16)
    result.append({'key': 'Counter', 'value': count})

    channel1 = (int(ByteToHex(message[7]), 16) * 0x100 + int(ByteToHex(message[8]), 16)) * 0.1
    result.append({'key': 'Channel #1', 'value': channel1, 'unit': 'A'})

    channel2 = (int(ByteToHex(message[9]), 16) * 0x100 + int(ByteToHex(message[10]), 16)) * 0.1
    result.append({'key': 'Channel #2', 'value': channel2, 'unit': 'A'})

    channel3 = (int(ByteToHex(message[11]), 16) * 0x100 + int(ByteToHex(message[12]), 16)) * 0.1
    result.append({'key': 'Channel #3', 'value': channel3, 'unit': 'A'})

    signal = rfxdecode.decode_signal(message[13])
    result.append({'key': 'Signal level', 'value': signal})

    battery = rfxdecode.decode_battery(message[13])
    result.append({'key': 'Battery', 'value': battery})

    output_extra = [
        ('id', sensor_id),
        ('counter', count),
        ('channel1', channel1),
        ('channel2', channel2),
        ('channel3', channel3),
        ('battery', battery),
        ('signal_level', signal)]

    return result, output_extra


def decode_0x5a(message, subtype, seqnbr, id1, id2):
    """
    0x5A Energy sensor
    Credit: Jean-Michel ROY
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_5A[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    count = int(ByteToHex(message[6]), 16)
    result.append({'key': 'Count', 'value': count})

    instant = int(ByteToHex(message[7]), 16) * 0x1000000 + \
              int(ByteToHex(message[8]), 16) * 0x10000 + \
              int(ByteToHex(message[9]), 16) * 0x100  + \
              int(ByteToHex(message[10]), 16)
    result.append({'key': 'Instant usage', 'value': instant})

    usage = int((
        int(ByteToHex(message[11]), 16) * 0x10000000000 + \
        int(ByteToHex(message[12]), 16) * 0x100000000 + \
        int(ByteToHex(message[13]), 16) * 0x1000000 + \
        int(ByteToHex(message[14]), 16) * 0x10000 + \
        int(ByteToHex(message[15]), 16) * 0x100 + \
        int(ByteToHex(message[16]), 16)) / 223.666)
    result.append({'key': 'Total usage', 'value': usage})

    signal = rfxdecode.decode_signal(message[17])
    result.append({'key': 'Signal level', 'value': signal})

    battery = rfxdecode.decode_battery(message[17])
    result.append({'key': 'Battery', 'value': battery})

    output_extra = [
        ('id', sensor_id),
        ('instant_usage', instant),
        ('total_usage', usage),
        ('battery', battery),
        ('signal_level', signal)]

    return result, output_extra


def decode_0x5b(message, subtype, seqnbr, id1, id2):
    """
    0x5B Current Sensor
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_5B[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    count = int(ByteToHex(message[6]), 16)
    result.append({'key': 'Counter', 'value': count})

    channel1 = (int(ByteToHex(message[7]), 16) * 0x100 + int(ByteToHex(message[8]), 16)) * 0.1
    result.append({'key': 'Channel #1', 'value': channel1, 'unit': 'A'})

    channel2 = (int(ByteToHex(message[9]), 16) * 0x100 + int(ByteToHex(message[10]), 16)) * 0.1
    result.append({'key': 'Channel #2', 'value': channel2, 'unit': 'A'})

    channel3 = (int(ByteToHex(message[11]), 16) * 0x100 + int(ByteToHex(message[12]), 16)) * 0.1
    result.append({'key': 'Channel #3', 'value': channel3, 'unit': 'A'})

    total = float((
        int(ByteToHex(message[13]), 16) * 0x10000000000 + \
        int(ByteToHex(message[14]), 16) * 0x100000000 + \
        int(ByteToHex(message[15]), 16) * 0x1000000 + \
        int(ByteToHex(message[16]), 16) * 0x10000 + \
        int(ByteToHex(message[17]), 16) * 0x100 + \
        int(ByteToHex(message[18]), 16)) / 223.666)
    result.append({'key': 'Total', 'value': total, 'unit': 'Wh'})

    signal = rfxdecode.decode_signal(message[19])
    result.append({'key': 'Signal level', 'value': signal})

    battery = rfxdecode.decode_battery(message[19])
    result.append({'key': 'Battery', 'value': battery})

    output_extra = [
        ('id', sensor_id),
        ('counter', count),
        ('channel1', channel1),
        ('channel2', channel2),
        ('channel3', channel3),
        ('total', total),
        ('battery', battery),
        ('signal_level', signal)]

    return result, output_extra


def decode_0x5c(message, subtype, seqnbr, id1, id2):
    """
    0x5C Power Sensors
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_5C[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    sensor_id = id1 + id2
    result.append({'key': 'Id', 'value': sensor_id})

    voltage = int(ByteToHex(message[6]), 16)
    result.append({'key': 'Voltage', 'value': voltage, 'unit': 'V'})

    current = (int(ByteToHex(message[7]), 16) * 0x100 + int(ByteToHex(message[8]), 16)) * 0.01
    result.append({'key': 'Current', 'value': current, 'unit': 'A'})

    power = (int(ByteToHex(message[9]), 16) * 0x100 + int(ByteToHex(message[10]), 16)) * 0.1
    result.append({'key': 'Instant power', 'value': power, 'unit': 'W'})

    energy = (int(ByteToHex(message[11]), 16) * 0x100 + int(ByteToHex(message[12]), 16)) * 0.01
    result.append({'key': 'Total usage', 'value': energy, 'unit': 'kWh'})

    powerfactor = (int(ByteToHex(message[13]), 16)) * 0.01
    result.append({'key': 'Power factor', 'value': powerfactor})

    freq = int(ByteToHex(message[14]), 16)
    result.append({'key': 'Frequency', 'value': freq, 'unit': 'Hz'})

    signal = rfxdecode.decode_signal(message[15])
    result.append({'key': 'Signal level', 'value': signal})

    output_extra = [
        ('id', sensor_id),
        ('voltage', voltage),
        ('current', current),
        ('instant_power', power),
        ('total_usage', energy),
        ('powerfactor', powerfactor),
        ('freq', freq),
        ('signal_level', signal)]

    return result, output_extra


def decode_0x5d(subtype, seqnbr):
    """
    0x5D
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_5D[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    return result, []


def decode_0x5e(subtype, seqnbr):
    """
    0x5E Gas Usage Sensor
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_5E[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    return result, []


def decode_0x5f(subtype, seqnbr):
    """
    0x5F Water Usage Sensor
    """

    result = list()

    try:
        display_subtype = RFX.rfx_subtype_5F[subtype]
    except KeyError:
        display_subtype = '0x' + subtype
    result.append({'key': 'Subtype', 'value': display_subtype})

    result.append({'key': 'Sequence number', 'value': seqnbr})

    return result, []
