#
#    Copyright (c) 2012 Tom Keffer <tkeffer@gmail.com> + m. bakker
#
#    See the file LICENSE.txt for your full rights.
#
#    $Revision: 1000 
#    $Author: tkeffer + mbakker 
#
"""Console RfxCmd for the weewx weather system"""

from __future__ import with_statement
import math
import time
import socket
import syslog
from datetime import datetime

import weedb
import weeutil.weeutil
import weewx.abstractstation
import weewx.wxformulas

# General decoding sensor maps.
WIND_DIR_MAP = { 0:'N', 1:'NNE', 2:'NE', 3:'ENE',
				4:'E', 5:'ESE', 6:'SE', 7:'SSE',
				8:'S', 9:'SSW', 10:'SW', 11:'WSW',
				12:'W', 13:'WNW', 14:'NW', 15:'NNW' }
FORECAST_MAP = { 0:'Partly Cloudy', 1:'Rainy', 2:'Cloudy', 3:'Sunny',
				4:'Clear Night', 5:'Snowy',
				6:'Partly Cloudy Night', 7:'Unknown7' }
HUMIDITY_STATUS = { "00":"Dry", "01":"Comfort", "02":"Normal", "03":"Wet"}		
TRENDS = { 0:'Stable', 1:'Rising', 2:'Falling', 3:'Undefined' }

def loader(config_dict, engine):
	"""Used to load the driver."""
	# The WMR driver needs the altitude in meters. Get it from the Station data
	# and do any necessary conversions.
	altitude_t = weeutil.weeutil.option_as_list( config_dict['Station'].get('altitude', (None, None)))
	# Form a value-tuple
	altitude_vt = (float(altitude_t[0]), altitude_t[1], 'group_altitude')
	# Now convert to meters, using only the first element of the returned 
	# value-tuple.
	altitude_m = weewx.units.convert(altitude_vt, 'meter')[0]
	
	station = RfxCmd(altitude=altitude_m, **config_dict['RfxCmd'])
	
	return station

class RfxCmd(weewx.abstractstation.AbstractStation):
	
	def to_bool(self, value):
		if str(value).lower() in ("yes", "y", "true",  "t", "1"): 
			return True
		if str(value).lower() in ("no",  "n", "false", "f", "0", "0.0", "", "none", "[]", "{}"): 
			return False
		raise Exception('Invalid value for boolean conversion: ' + str(value))
	
	def writelog(self, string):
		if self.rfx_logfile and self.rfx_debug:
			try:
				timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				f = open(self.rfx_logfile,'a+')
				f.write(timestamp + " - " + string + "\n")
				f.close()
			except Exception as err:
				syslog.syslog(syslog.LOG_ERR, "RfxCmd: Could not write to logfile" % (str(self.rfx_logfile)))
				syslog.syslog(syslog.LOG_ERR, "RfxCmd: Exception -  " % (str(err)))
				pass
	
	def __init__(self, **stn_dict):
		
		"""Initialize """ 
		# Debug
		self.rfx_debug = self.to_bool(stn_dict.get('debug', False))
		self.rfx_logfile = stn_dict.get('logfile', None)
		
		self.writelog("----------------------------------")
		self.writelog("Init RFXcmd sensor data collection")
		
		self.altitude = stn_dict['altitude']
		self.writelog("Altitude = %s" % str(self.altitude))
		self.mode = stn_dict['mode']
		self.writelog("Mode = %s" % str(self.mode))
		
		self.last_totalRain = None
		
		# RFXcmd Socket data
		self.socket_server = stn_dict.get('socket_server', 'localhost')
		self.writelog("Socket server = %s" % str(self.socket_server))
		self.socket_port = int(stn_dict.get('socket_port', 55000))
		self.writelog("Socket port = %s" % str(self.socket_port))
		self.socket_message = stn_dict.get('socket_message', '0A1100FF001100FF001100')
		
		# Sensor
		self.legacy = self.to_bool(stn_dict.get('legacy', False))
		
		# 0x4F Temp and Rain sensors
		self.sensor_0x4F = self.to_bool(stn_dict.get('sensor_0x4F', False))
		self.writelog("Sensor 0x4f = %s" % str(self.sensor_0x4F))
		self.sensor_0x4F_temp = stn_dict.get('sensor_0x4F_temp', False)
		self.sensor_0x4F_raintotal = stn_dict.get('sensor_0x4F_raintotal', False)
		self.sensor_0x4F_batt = stn_dict.get('sensor_0x4F_batt', False)
		self.sensor_0x4F_rssi = stn_dict.get('sensor_0x4F_rssi', False)
		
		# 0x50 Temperature Sensors
		self.sensor_0x50 = self.to_bool(stn_dict.get('sensor_0x50', False))
		self.writelog("Sensor 0x50 = %s" % str(self.sensor_0x50))
		self.sensor_0x50_temp = stn_dict.get('sensor_0x50_temp', False)
		self.sensor_0x50_batt = stn_dict.get('sensor_0x50_batt', False)
		self.sensor_0x50_rssi = stn_dict.get('sensor_0x50_rssi', False)
		
		# 0x51 Humidity Sensors
		self.sensor_0x51 = self.to_bool(stn_dict.get('sensor_0x51', False))
		self.writelog("Sensor 0x51 = %s" % str(self.sensor_0x51))
		self.sensor_0x51_hum = stn_dict.get('sensor_0x51_hum', False)
		self.sensor_0x51_batt = stn_dict.get('sensor_0x51_batt', False)
		self.sensor_0x51_rssi = stn_dict.get('sensor_0x51_rssi', False)
		
		# 0x52 Temp/Baro Sensors
		self.sensor_0x52 = self.to_bool(stn_dict.get('sensor_0x52', False))
		self.writelog("Sensor 0x52 = %s" % str(self.sensor_0x52))
		self.sensor_0x52_temp = stn_dict.get('sensor_0x52_temp', False)
		self.sensor_0x52_hum = stn_dict.get('sensor_0x52_hum', False)
		self.sensor_0x52_batt = stn_dict.get('sensor_0x52_batt', False)
		self.sensor_0x52_rssi = stn_dict.get('sensor_0x52_rssi', False)
		
		# 0x53 Barometric Sensors
		self.sensor_0x53 = self.to_bool(stn_dict.get('sensor_0x53', False))
		self.writelog("Sensor 0x53 = %s" % str(self.sensor_0x53))
		self.sensor_0x53_baro = stn_dict.get('sensor_0x53_baro', False)
		self.sensor_0x53_batt = stn_dict.get('sensor_0x53_batt', False)
		self.sensor_0x53_rssi = stn_dict.get('sensor_0x53_rssi', False)
		
		# 0x54 Temp/Hum/Baro Sensors
		self.sensor_0x54 = self.to_bool(stn_dict.get('sensor_0x54', False))
		self.writelog("Sensor 0x54 = %s" % str(self.sensor_0x54))
		self.sensor_0x54_temp = stn_dict.get('sensor_0x54_temp', False)
		self.sensor_0x54_hum = stn_dict.get('sensor_0x54_hum', False)
		self.sensor_0x54_baro = stn_dict.get('sensor_0x54_baro', False)
		self.sensor_0x54_batt = stn_dict.get('sensor_0x54_batt', False)
		self.sensor_0x54_rssi = stn_dict.get('sensor_0x54_rssi', False)
		
		# 0x55 Rain Sensors
		self.sensor_0x55 = self.to_bool(stn_dict.get('sensor_0x55', False))
		self.writelog("Sensor 0x55 = %s" % str(self.sensor_0x55))
		self.sensor_0x55_rainrate = stn_dict.get('sensor_0x55_rainrate', False)
		self.sensor_0x55_raintotal = stn_dict.get('sensor_0x55_raintotal', False)
		self.sensor_0x55_batt = stn_dict.get('sensor_0x55_batt', False)
		self.sensor_0x55_rssi = stn_dict.get('sensor_0x55_rssi', False)
		
		# 0x56 Wind Sensors
		self.sensor_0x56 = self.to_bool(stn_dict.get('sensor_0x56', False))
		self.writelog("Sensor 0x56 = %s" % str(self.sensor_0x56))
		self.sensor_0x56_direction = stn_dict.get('sensor_0x56_direction', False)
		self.sensor_0x56_avspeed = stn_dict.get('sensor_0x56_avspeed', False)
		self.sensor_0x56_gust = stn_dict.get('sensor_0x56_gust', False)
		self.sensor_0x56_temp = stn_dict.get('sensor_0x56_temp', False)
		self.sensor_0x56_chill = stn_dict.get('sensor_0x56_chill', False)
		self.sensor_0x56_batt = stn_dict.get('sensor_0x56_batt', False)
		self.sensor_0x56_rssi = stn_dict.get('sensor_0x56_rssi', False)
		
		# Sensor 0x57 UV
		self.sensor_0x57 = self.to_bool(stn_dict.get('sensor_0x57', False))
		self.writelog("Sensor 0x57 = %s" % str(self.sensor_0x57))
		self.sensor_0x57_uv = stn_dict.get('sensor_0x57_uv', False)
		self.sensor_0x57_temp = stn_dict.get('sensor_0x57_temp', False)
		self.sensor_0x57_batt = stn_dict.get('sensor_0x57_batt', False)
		self.sensor_0x57_rssi = stn_dict.get('sensor_0x57_rssi', False)
		
		self.stale_wind = int(stn_dict.get('stale_wind', 30))
		self.writelog("Stale wind = %s " % str(self.stale_wind))
		self.loop_interval = float(stn_dict.get('loop_interval', 60))
		self.writelog("Loop interval = %s " % str(self.loop_interval))
		start_ts = self.the_time = time.time()
		self.writelog("Init done")
	
	def get_rfxdata(self, sensor):
		syslog.syslog(syslog.LOG_ERR, "RfxCmd: Get data")
		
		data = None
		rbufsize = -1
		wbufsize = 0
		packet_recv = False
		sock = None
		
		self.writelog("Get data for sensor %s " % str(sensor))
		message = "WEEWX;" + sensor
		self.writelog("Remote: %s:%s" % (str(self.socket_server), str(self.socket_port)))
		self.writelog("Open socket connection")
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((self.socket_server, self.socket_port))
			self.writelog("Socket OK")
		except Exception as err:
			self.writelog("Exception: %s " % str(err))
			syslog.syslog(syslog.LOG_ERR, "RfxCmd: Exception: %s " % str(err))
			data = None
			sock = None
			pass
		
		if sock:
			try:
				self.writelog("Send socket command = %s" % str(message))
				rfile = sock.makefile('rb', rbufsize)
				wfile = sock.makefile('wb', wbufsize)
				wfile.write( message +"\n" )
				data = rfile.read()
				self.writelog("Received data: %s " % str(data))
				self.writelog("Close socket")
				sock.close()
			except socket.error as err:
				data = None
				self.writelog("Error: Failed to connect to remote")
				self.writelog("Exception: %s " % str(err))
				syslog.syslog(syslog.LOG_ERR, "RfxCmd: Exception: %s " % str(err))
				pass
		
		if data:
			return data
		else:
			return None
		
	def genLoopPackets(self):
		while True:
			# Determine how long to sleep
			# We are in real time mode. Try to keep synched up with the
			# wall clock
			sleep_time = self.the_time + self.loop_interval - time.time()
			if sleep_time > 0: 
				time.sleep(sleep_time)
			
			# Update the simulator clock:
			self.the_time += self.loop_interval
			packet_recv = 0
			
			# --------------------------------------------------------------------------------------
			# Sensor 0x52 
			# --------------------------------------------------------------------------------------
			if bool(self.sensor_0x52):
				self.writelog("0x52: --- Start ---")
				result = None
				_packet = {'dateTime': int(self.the_time+0.5), 'usUnits' : weewx.METRIC }
				result = self.get_rfxdata("0x52")
				self.writelog("0x52: Data: %s " % str(result))
				if result:
					data = result.split(';')
					if not bool(self.sensor_0x52_temp) == False:
						self.writelog("0x52: %s = %s" % (str(self.sensor_0x52_temp), (str(data[0]))))
						_packet[self.sensor_0x52_temp] = float(data[0])
					
					if not bool(self.sensor_0x52_hum) == False:
						self.writelog("0x52: %s = %s" % (str(self.sensor_0x52_hum), (str(data[1]))))
						_packet[self.sensor_0x52_hum] = float(data[1])
					
					if not bool(self.sensor_0x52_batt) == False:
						self.writelog("0x52: %s = %s" % (str(self.sensor_0x52_batt), (str(data[2]))))
						_packet[self.sensor_0x52_batt] = float(data[2])
					
					if not bool(self.sensor_0x52_rssi) == False:
						self.writelog("0x52: %s = %s" % (str(self.sensor_0x52_rssi), (str(data[3]))))
						_packet[self.sensor_0x52_rssi] = float(data[3])
					
					_packet['dewpoint'] = weewx.wxformulas.dewpointC(_packet[self.sensor_0x52_temp], _packet[self.sensor_0x52_hum])
					_packet['heatindex'] = weewx.wxformulas.heatindexC(_packet[self.sensor_0x52_temp], _packet[self.sensor_0x52_hum])	
					OT = _packet[self.sensor_0x52_temp]
					
					yield _packet
					self.writelog("0x52: --- End ---")
				else:
					self.writelog("0x52: Result None, no process")
			
			# --------------------------------------------------------------------------------------
			# Sensor 0x53 
			# --------------------------------------------------------------------------------------
			if bool(self.sensor_0x53):
				self.writelog("0x53: --- Start ---")
				result = None
				_packet = {'dateTime': int(self.the_time+0.5), 'usUnits' : weewx.METRIC }
				result = self.get_rfxdata("0x53")
				self.writelog("0x53: Data: %s " % str(result))
				if result:
					data = result.split(';')
					if not bool(self.sensor_0x53_baro) == False:
						self.writelog("0x53: %s = %s" % (str(self.sensor_0x53_hum), (str(data[1]))))
						_packet[self.sensor_0x53_baro] = float(data[1])
					
					if not bool(self.sensor_0x53_batt) == False:
						self.writelog("0x53: %s = %s" % (str(self.sensor_0x53_batt), (str(data[2]))))
						_packet[self.sensor_0x53_batt] = float(data[2])
					
					if not bool(self.sensor_0x53_rssi) == False:
						self.writelog("0x53: %s = %s" % (str(self.sensor_0x53_rssi), (str(data[3]))))
						_packet[self.sensor_0x53_rssi] = float(data[3])
					
					yield _packet
					self.writelog("0x53: --- End ---")
				else:
					self.writelog("0x53: Result None, no process")
			
			# --------------------------------------------------------------------------------------
			# Sensor 0x54
			# --------------------------------------------------------------------------------------
			if bool(self.sensor_0x54):
				self.writelog("0x54: --- Start ---")
				result = None
				_packet = {'dateTime': int(self.the_time+0.5), 'usUnits' : weewx.METRIC }
				result = self.get_rfxdata("0x54")
				self.writelog("0x54: Data: %s " % str(result))
				if result:
					data = result.split(';')
					if not bool(self.sensor_0x54_temp) == False:
						self.writelog("0x54: %s = %s" % (str(self.sensor_0x54_temp), (str(data[0]))))
						_packet[self.sensor_0x54_temp] = float(data[0])
					
					if not bool(self.sensor_0x54_hum) == False:
						self.writelog("0x54: %s = %s" % (str(self.sensor_0x54_hum), (str(data[1]))))
						_packet[self.sensor_0x54_hum] = float(data[1])
					
					if not bool(self.sensor_0x54_baro) == False:
						self.writelog("0x54: %s = %s" % (str(self.sensor_0x54_baro), (str(data[1]))))
						_packet[self.sensor_0x54_baro] = float(data[2])
					
					if not bool(self.sensor_0x54_batt) == False:
						self.writelog("0x54: %s = %s" % (str(self.sensor_0x54_batt), (str(data[2]))))
						_packet[self.sensor_0x54_batt] = float(data[3])
					
					if not bool(self.sensor_0x54_rssi) == False:
						self.writelog("0x54: %s = %s" % (str(self.sensor_0x54_rssi), (str(data[3]))))
						_packet[self.sensor_0x54_rssi] = float(data[4])
					
					SA = weewx.wxformulas.altimeter_pressure_Metric(_packet[self.sensor_0x54_baro], self.altitude)
					_packet['altimeter'] = SA
					
					yield _packet
					self.writelog("0x54: --- End ---")
				else:
					self.writelog("0x54: Result None, no process")
			
			# --------------------------------------------------------------------------------------
			# Sensor 0x55
			# --------------------------------------------------------------------------------------
			if bool(self.sensor_0x55):
				self.writelog("0x55: --- Start ---")
				result = None
				_packet = {'dateTime': int(self.the_time+0.5), 'usUnits' : weewx.METRIC }
				result = self.get_rfxdata("0x55")
				self.writelog("0x55: Data: %s " % str(result))
				if result:
					data = result.split(';')
					if not bool(self.sensor_0x55_rainrate) == False:
						self.writelog("0x55: %s = %s" % (str(self.sensor_0x55_rainrate), (str(data[0]))))
						_packet[self.sensor_0x55_rainrate] = float(data[0])
					
					if not bool(self.sensor_0x55_raintotal) == False:
						self.writelog("0x55: %s = %s" % (str(self.sensor_0x55_raintotal), (str(data[1]))))
						_packet[self.sensor_0x55_raintotal] = float(data[1])
					
					if not bool(self.sensor_0x55_batt) == False:
						self.writelog("0x55: %s = %s" % (str(self.sensor_0x55_batt), (str(data[2]))))
						_packet[self.sensor_0x55_batt] = float(data[2])
					
					if not bool(self.sensor_0x55_rssi) == False:
						self.writelog("0x55: %s = %s" % (str(self.sensor_0x55_rssi), (str(data[3]))))
						_packet[self.sensor_0x55_rssi] = float(data[3])
					
					_packet['rain'] = ((_packet[self.sensor_0x55_raintotal]-self.last_totalRain)/10) if self.last_totalRain is not None else None
					
					if _packet['rain'] == _packet[self.sensor_0x55_raintotal]:
						_packet['rain'] = None
					
					self.last_totalRain = _packet[self.sensor_0x55_raintotal]
					
					yield _packet
					self.writelog("0x55: --- End ---")
				else:
					self.writelog("0x55: Result None, no process")
					
			# --------------------------------------------------------------------------------------
			# Sensor 0x56
			# --------------------------------------------------------------------------------------
			if bool(self.sensor_0x56):
				self.writelog("0x56: --- Start ---")
				result = None
				_packet = {'dateTime': int(self.the_time+0.5), 'usUnits' : weewx.METRICWX }
				result = self.get_rfxdata("0x56")
				self.writelog("0x56: Data: %s " % str(result))
				if result:
					data = result.split(';')
					if not bool(self.sensor_0x56_direction) == False:
						self.writelog("0x56: %s = %s" % (str(self.sensor_0x56_direction), (str(data[0]))))
						_packet[self.sensor_0x56_direction] = float(data[0])
					
					if not bool(self.sensor_0x56_avspeed) == False:
						self.writelog("0x56: %s = %s" % (str(self.sensor_0x56_avspeed), (str(data[1]))))
						_packet[self.sensor_0x56_avspeed] = float(data[1])
					
					if not bool(self.sensor_0x56_temp) == False:
						if not data[2] == "None":
							self.writelog("0x56: %s = %s" % (str(self.sensor_0x56_temp), (str(data[2]))))
							_packet[self.sensor_0x56_temp] = float(data[2])
					
					if not bool(self.sensor_0x56_gust) == False:
						self.writelog("0x56: %s = %s" % (str(self.sensor_0x56_gust), (str(data[3]))))
						_packet[self.sensor_0x56_gust] = float(data[3])
						
					if not bool(self.sensor_0x56_chill) == False:
						if not data[4] == "None":
							self.writelog("0x56: %s = %s" % (str(self.sensor_0x56_chill), (str(data[4]))))
							_packet[self.sensor_0x56_chill] = float(data[4])
							
					if not bool(self.sensor_0x56_batt) == False:
						self.writelog("0x56: %s = %s" % (str(self.sensor_0x56_batt), (str(data[5]))))
						_packet[self.sensor_0x56_batt] = float(data[5])
					
					if not bool(self.sensor_0x56_rssi) == False:
						self.writelog("0x56: %s = %s" % (str(self.sensor_0x56_rssi), (str(data[6]))))
						_packet[self.sensor_0x56_rssi] = float(data[6])
						
					
					if _packet[self.sensor_0x56_avspeed] == 0:
						_packet[self.sensor_0x56_direction] = None
						
					_packet['windchill'] = weewx.wxformulas.windchillC(OT, _packet[self.sensor_0x56_avspeed])
					
					yield _packet
					self.writelog("0x56: --- End ---")
				else:
					self.writelog("0x56: Result None, no process")
			
			# --------------------------------------------------------------------------------------
			# Sensor 0x57 UV
			# --------------------------------------------------------------------------------------
			if bool(self.sensor_0x57):
				self.writelog("0x57: --- Start ---")
				result = None
				_packet = {'dateTime': int(self.the_time+0.5), 'usUnits' : weewx.METRIC }
				result = self.get_rfxdata("0x57")
				self.writelog("0x57: Data: %s " % str(result))
				if result:
					data = result.split(';')
					if not bool(self.sensor_0x57_uv) == False:
						self.writelog("0x57: %s = %s" % (str(self.sensor_0x57_uv), (str(data[0]))))
						_packet[self.sensor_0x57_uv] = float(data[0])
					
					if not bool(self.sensor_0x57_temp) == False:
						if not data[1] == "None":
							self.writelog("0x57: %s = %s" % (str(self.sensor_0x57_temp), (str(data[1]))))
							_packet[self.sensor_0x57_temp] = float(data[1])
					
					if not bool(self.sensor_0x57_batt) == False:
						self.writelog("0x57: %s = %s" % (str(self.sensor_0x57_batt), (str(data[2]))))
						_packet[self.sensor_0x57_batt] = float(data[2])
					
					if not bool(self.sensor_0x57_rssi) == False:
						self.writelog("0x57: %s = %s" % (str(self.sensor_0x57_rssi), (str(data[3]))))
						_packet[self.sensor_0x57_rssi] = float(data[3])
					
					yield _packet
					self.writelog("0x57: --- End ---")
				else:
					self.writelog("0x57: Result None, no process")
			
			'''
			# Update weather_data:
			if bool(self.legacy) == True:
				try:
					syslog.syslog(syslog.LOG_ERR, "rfxcmd: Get data")
					data= ''
					rbufsize= -1
					wbufsize= 0
					sock = None
					syslog.syslog(syslog.LOG_ERR, "rfxcmd: Server = %s, Port = %s " % (str(self.socket_server), str(self.socket_port)))	
					sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					sock.connect((self.socket_server, self.socket_port))
					rfile = sock.makefile('rb', rbufsize)
					wfile = sock.makefile('wb', wbufsize)	
					wfile.write( self.socket_message +"\n" )
					syslog.syslog(syslog.LOG_ERR, "rfxcmd: Socket message: %s " % str(self.socket_message))
					data= rfile.read()
					sock.close()
					sd = data.split("|")
					packet_recv = 1
				except socket.error as err:
					syslog.syslog(syslog.LOG_ERR, "rfxcmd: Failed to connect!")
					syslog.syslog(syslog.LOG_ERR, "rfxcmd: Error: %s " % str(err))
					pass
				
				if packet_recv == 1:
					syslog.syslog(syslog.LOG_ERR, "rfxcmd: Received %s " % str(sd))
					_packet = {'dateTime': int(self.the_time+0.5), 'usUnits' : weewx.METRIC }
				
					if sd[3] != '0':
						_packet['windSpeed'] = float(sd[5])
						_packet['windDir'] = float(sd[4])
						_packet['windGust'] = float(sd[6])
				
					if sd[11] != '0':
						_packet['outTemp'] = float(sd[12])
						_packet['outHumidity'] = float(sd[13])
						_packet['dewpoint'] = weewx.wxformulas.dewpointC(_packet['outTemp'], _packet['outHumidity'])
						_packet['heatindex'] = weewx.wxformulas.heatindexC(_packet['outTemp'], _packet['outHumidity'])
				
					if sd[19] != '0':
						_packet['inTemp'] = float(sd[20])
						_packet['inHumidity'] = float(sd[21])
						_packet['pressure'] = float(sd[23])
						SA = weewx.wxformulas.altimeter_pressure_Metric(_packet['pressure'], self.altitude)
						_packet['altimeter'] = SA
				
					if sd[29] != '0':
						_packet['rain'] = float(sd[30])
						_packet['UV'] = float(sd[40])
				
					if sd[3] != '0' and sd[11] != '0':
						_packet['windchill'] = weewx.wxformulas.windchillC(_packet['outTemp'], _packet['windSpeed'])
				
					_packet['inTempBatteryStatus'] = 1.0
					_packet['OutTempBatteryStatus'] = 1.0
					_packet['rainBatteryStatus'] = 1.0
					_packet['windBatteryStatus'] = 1.0
					_packet['txBatteryStatus'] = 1.0
					_packet['rxCheckPercent'] = 1.0
				
					if float(sd[7]) < 2:
						_packet['windBatteryStatus'] = 0
				
					if float(sd[15]) < 2:
						_packet['OutTempBatteryStatus'] = 0
					
					if float(sd[25]) < 2:
						_packet['InTempBatteryStatus'] = 0
				
					if float(sd[35]) < 2:
						_packet['rainBatteryStatus'] = 0
					
					yield _packet
					syslog.syslog(syslog.LOG_NOTICE, "rfxcmd: stored new data.")
			'''
			
	def getTime(self):
		return self.the_time
	
	@property
	def hardware_name(self):
		return "RfxCmd"

if __name__ == "__main__":
	station = RfxCmd(mode='simulator',loop_interval=2.0)
	for packet in station.genLoopPackets():
		print weeutil.weeutil.timestamp_to_string(packet['dateTime']), packet
