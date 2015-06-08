#!/usr/bin/python
# -*- coding:utf-8 -*-
 
# ------------------------------------------------------------------------------
#	
#	RFX_WEEWX.PY
#	
#	Copyright (C) 2013 M. Bakker
#
#	Class weewx_data, needed for sending answer at request of 
#	WEEWX Weatherstation software
#	
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#	
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#	
#	Website
#	http://code.google.com/p/rfxcmd/
#
#	$Rev: 464 $
#	$Date: 2013-05-01 22:41:36 +0200 (Wed, 01 May 2013) $
#
# ------------------------------------------------------------------------------

# --------------------------------------------------------------------------

import logging
logger = logging.getLogger('rfxcmd')

class weewx_data:
	def __init__(
		self,
		wwx_wind_dir = 0,
		wwx_wind_avg = 0,
		wwx_wind_gust = 0,
		wwx_wind_batt = 0,
		wwx_wind_sign = 0,
		wwx_th_t_out = 0,
		wwx_th_h_out = 0,
		wwx_th_hs_out = 0,
		wwx_th_batt = 0,
		wwx_th_sign = 0,
		wwx_thb_t_in = 0,
		wwx_thb_h_in = 0,
		wwx_thb_hs_in = 0,
		wwx_thb_b_in = 0,
		wwx_thb_fs_in = 0,
		wwx_thb_batt = 0,
		wwx_thb_sign = 0,
		wwx_rain_rate = 0,
		wwx_rain_batt = 0,
		wwx_rain_sign = 0,
		wwx_uv_out = 0,
		wwx_uv_batt = 0,
		wwx_uv_sign = 0,
		# 0x4F Temperature and Rain sensor
		wwx_0x4f_temp = 0,
		wwx_0x4f_raintotal = 0,
		wwx_0x4f_batt = 0,
		wwx_0x4f_rssi = 0,
		# 0x50 Temperature sensor
		wwx_0x50_temp = 0,
		wwx_0x50_batt = 0,
		wwx_0x50_rssi = 0,
		# 0x51 Humidity sensor
		wwx_0x51_hum = 0,
		wwx_0x51_batt = 0,
		wwx_0x51_rssi = 0,
		# 0x52 Temperature and Barometric sensor
		wwx_0x52_temp = 0,
		wwx_0x52_hum = 0,
		wwx_0x52_batt = 0,
		wwx_0x52_rssi = 0,
		# 0x53 Barometric sensor
		wwx_0x53_baro = 0,
		wwx_0x53_batt = 0,
		wwx_0x53_rssi = 0,
		# 0x54 Temp/Hum/Baro sensor
		wwx_0x54_temp = 0,
		wwx_0x54_hum = 0,
		wwx_0x54_baro = 0,
		wwx_0x54_batt = 0,
		wwx_0x54_rssi = 0,
		# 0x55 Rain sensor
		wwx_0x55_rainrate = 0,
		wwx_0x55_raintotal = 0,
		wwx_0x55_batt = 0,
		wwx_0x55_rssi = 0,
		# 0x56 Wind sensor
		wwx_0x56_direction = 0,
		wwx_0x56_avspeed = 0,
		wwx_0x56_gust = 0,
		wwx_0x56_temp = 0,
		wwx_0x56_chill = 0,
		wwx_0x56_batt = 0,
		wwx_0x56_rssi = 0,
		# 0x57 UV sensor
		wwx_0x57_uv = 0,
		wwx_0x57_temp = 0,
		wwx_0x57_batt = 0,
		wwx_0x57_rssi = 0
		):
		
		self.wwx_wind_dir = wwx_wind_dir
		self.wwx_wind_avg = wwx_wind_avg
		self.wwx_wind_gust = wwx_wind_gust
		self.wwx_wind_batt = wwx_wind_batt
		self.wwx_wind_sign = wwx_wind_sign
		self.wwx_th_t_out = wwx_th_t_out
		self.wwx_th_h_out = wwx_th_h_out
		self.wwx_th_hs_out = wwx_th_hs_out
		self.wwx_th_batt = wwx_th_batt
		self.wwx_th_sign = wwx_th_sign
		self.wwx_thb_t_in = wwx_thb_t_in
		self.wwx_thb_h_in = wwx_thb_h_in
		self.wwx_thb_hs_in = wwx_thb_hs_in
		self.wwx_thb_b_in = wwx_thb_b_in
		self.wwx_thb_fs_in = wwx_thb_fs_in
		self.wwx_thb_batt = wwx_thb_batt
		self.wwx_thb_sign = wwx_thb_sign
		self.wwx_rain_rate = wwx_rain_rate
		self.wwx_rain_batt = wwx_rain_batt
		self.wwx_rain_sign = wwx_rain_sign
		self.wwx_uv_out = wwx_uv_out
		self.wwx_uv_batt = wwx_uv_batt
		self.wwx_uv_sign = wwx_uv_sign
		
		# 0x4F Temperature and Rain sensor
		self.wwx_0x4f_temp = wwx_0x4f_temp
		self.wwx_0x4f_raintotal = wwx_0x4f_raintotal
		self.wwx_0x4f_batt = wwx_0x4f_batt
		self.wwx_0x4f_rssi = wwx_0x4f_rssi
		
		# 0x50 Temperature sensor
		self.wwx_0x50_temp = wwx_0x50_temp
		self.wwx_0x50_batt = wwx_0x50_batt
		self.wwx_0x50_rssi = wwx_0x50_rssi
		
		# 0x51 Humidity sensor
		self.wwx_0x51_hum = wwx_0x51_hum
		self.wwx_0x51_batt = wwx_0x51_batt
		self.wwx_0x51_rssi = wwx_0x51_rssi
		
		# 0x52 Temperature and Barometric sensor
		self.wwx_0x52_temp = wwx_0x52_temp
		self.wwx_0x52_hum = wwx_0x52_hum
		self.wwx_0x52_batt = wwx_0x52_batt
		self.wwx_0x52_rssi = wwx_0x52_rssi
		
		# 0x53 Barometric sensor
		self.wwx_0x53_baro = wwx_0x53_baro
		self.wwx_0x53_batt = wwx_0x53_batt
		self.wwx_0x53_rssi = wwx_0x53_rssi
		
		# 0x54 Temp/Hum/Baro sensor
		self.wwx_0x54_temp = wwx_0x54_temp
		self.wwx_0x54_hum = wwx_0x54_hum
		self.wwx_0x54_baro = wwx_0x54_baro
		self.wwx_0x54_batt = wwx_0x54_batt
		self.wwx_0x54_rssi = wwx_0x54_rssi
		
		# 0x55 Rain sensor
		self.wwx_0x55_rainrate = wwx_0x55_rainrate
		self.wwx_0x55_raintotal = wwx_0x55_raintotal
		self.wwx_0x55_batt = wwx_0x55_batt
		self.wwx_0x55_rssi = wwx_0x55_rssi
		
		# 0x56 Wind sensor
		self.wwx_0x56_direction= wwx_0x56_direction
		self.wwx_0x56_avspeed = wwx_0x56_avspeed
		self.wwx_0x56_temp = wwx_0x56_temp
		self.wwx_0x56_gust = wwx_0x56_gust
		self.wwx_0x56_chill = wwx_0x56_chill
		self.wwx_0x56_batt = wwx_0x56_batt
		self.wwx_0x56_rssi = wwx_0x56_rssi
		
		# 0x57 UV Sensor
		self.wwx_0x57_uv = wwx_0x57_uv
		self.wwx_0x57_temp = wwx_0x57_temp
		self.wwx_0x57_batt = wwx_0x57_batt
		self.wwx_0x57_rssi = wwx_0x57_rssi
	
	def weewx_result(self):
		result = '|'
		result = result + str(wwx.wwx_wind_dir) + '|' + str(wwx.wwx_wind_avg) + '|' + str(wwx.wwx_wind_gust)
		result = result + '|' + str(wwx.wwx_wind_batt) + '|' + str(wwx.wwx_wind_sign)
		result = result + '|' + str(wwx.wwx_th_t_out) + '|' + str(wwx.wwx_th_h_out) + '|' + str(wwx.wwx_th_hs_out)
		result = result + '|' + str(wwx.wwx_th_batt) + '|' + str(wwx.wwx_th_sign)
		result = result + '|' + str(wwx.wwx_thb_t_in) + '|' + str(wwx.wwx_thb_h_in)
		result = result + '|' + str(wwx.wwx_thb_hs_in) + '|' + str(wwx.wwx_thb_b_in)
		result = result + '|' + str(wwx.wwx_thb_fs_in) + '|' + str(wwx.wwx_thb_batt) + '|' + str(wwx.wwx_thb_sign)
		result = result + '|' + str(wwx.wwx_rain_rate) + '|' + str(wwx.wwx_rain_batt) + '|' + str(wwx.wwx_rain_sign)
		result = result + '|' + str(wwx.wwx_uv_out) + '|' + str(wwx.wwx_uv_batt) + '|' + str(wwx.wwx_uv_sign)
		result = result + '|'
		return result

	# 0x52 Temp/Hum Sensor
	def weewx_0x52(self):
		result = None
		result = "%s;%s;%s;%s" % (str(wwx.wwx_0x52_temp),str(wwx.wwx_0x52_hum),str(wwx.wwx_0x52_batt),str(wwx.wwx_0x52_rssi))
		logger.debug("Weewx.0x52=%s" % str(result))
		return result

	# 0x53 Barometric Sensor
	def weewx_0x53(self):
		result = None
		result = "%s;%s;%s" % (str(wwx.wwx_0x53_baro),str(wwx.wwx_0x53_batt),str(wwx.wwx_0x53_rssi))
		logger.debug("Weewx.0x53=%s" % str(result))
		return result

	# 0x54 Temp/Hum/Baro Sensor
	def weewx_0x54(self):
		result = None
		result = "%s;%s;%s;%s;%s" % (str(wwx.wwx_0x54_temp),str(wwx.wwx_0x54_hum),str(wwx.wwx_0x54_baro),str(wwx.wwx_0x54_batt),str(wwx.wwx_0x54_rssi))
		logger.debug("Weewx.0x54=%s" % str(result))
		return result
		
	# 0x55 Rain Sensor
	def weewx_0x55(self):
		result = None
		result = "%s;%s;%s;%s" % (str(wwx.wwx_0x55_rainrate),str(wwx.wwx_0x55_raintotal),str(wwx.wwx_0x55_batt),str(wwx.wwx_0x55_rssi))
		logger.debug("Weewx.0x55=%s" % str(result))
		return result	
		
	# 0x56 Wind Sensor
	def weewx_0x56(self):
		result = None
		result = "%s;%s;%s;%s;%s;%s;%s" % (str(wwx.wwx_0x56_direction),str(wwx.wwx_0x56_avspeed),str(wwx.wwx_0x56_temp),str(wwx.wwx_0x56_gust),str(wwx.wwx_0x56_chill),str(wwx.wwx_0x56_batt),str(wwx.wwx_0x56_rssi))
		logger.debug("Weewx.0x56=%s" % str(result))
		return result
	
	# 0x57 UV Sensor
	def weewx_0x57(self):
		result = None
		result = "%s;%s;%s;%s" % (str(wwx.wwx_0x57_uv),str(wwx.wwx_0x57_temp),str(wwx.wwx_0x57_batt),str(wwx.wwx_0x57_rssi))
		logger.debug("Weewx.0x57=%s" % str(result))
		return result
	
wwx = weewx_data()

# --------------------------------------------------------------------------
