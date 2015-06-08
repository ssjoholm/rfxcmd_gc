#!/usr/bin/python
# coding=UTF-8

# ------------------------------------------------------------------------------
#	
#	RFX_RRD.PY
#	
#	2013 Serge Tchesmeli, serge.tchesmeli@gmail.com
#	This is my modest contribution to rfxcmd :)
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

# ------------------------------------------------------------------------------

try:
	import rrdtool
except ImportError:
	pass

import os

def rrd1Metric (sensortype, sensorid, metric1, rrd_root):
	
	DS1 = "metric1"
	
	# ensure rrd dir exist
	if not os.path.exists (rrd_root):
		os.makedirs(rrd_root)
	
	# One dirs per sensor type, one rrd per sensor
	# If dir doesn't exist, create it.
	rrd_path = rrd_root + "/"+ sensortype +"/"
	if not os.path.exists(rrd_path):
		os.makedirs(rrd_path)
	rrdfile = rrd_path + sensorid + ".rrd"
	rrdfile = str(rrdfile)
	
	# If rrdfile doesn't exist, create it
	if not os.path.exists(rrdfile):
		# Legend depends of sensor type
		# 5A: Energy
		if sensortype == '5A' :
			DS1 = "Watt"
		
		# Create the rrd
		rrdtool.create(rrdfile, '--step', '30', '--start', '0', 'DS:%s:GAUGE:120:U:U' % (DS1), 'RRA:AVERAGE:0.5:1:1051200', 'RRA:AVERAGE:0.5:10:210240')
	
	# Update the rdd with new values
	rrdtool.update('%s' % (rrdfile), 'N:%s' % (metric1) )

def rrd2Metrics (sensortype, sensorid, metric1, metric2, rrd_root):
	
	DS1 = "metric1"
	DS2 = "metric2"
	
	# ensure rrd dir exist
	if not os.path.exists (rrd_root):
		os.makedirs(rrd_root)
	
	# One dirs per sensor type, one rrd per sensor
	# If dir doesn't exist, create it.
	rrd_path = rrd_root + "/"+ sensortype +"/"
	if not os.path.exists(rrd_path):
		os.makedirs(rrd_path)
	rrdfile = rrd_path + sensorid + ".rrd"
	rrdfile = str(rrdfile)
	
	# If rrdfile doesn't exist, create it
	if not os.path.exists(rrdfile):	
		# Legend depends of sensor type
		# 52: Temperature and humidity
		if sensortype == '52' :
			DS1 = "Temperature"
			DS2 = "Humidity"
		
		# Create the rrd
		rrdtool.create(rrdfile, '--step', '30', '--start', '0', 'DS:%s:GAUGE:120:U:U' % (DS1), 'DS:%s:GAUGE:120:U:U' % (DS2), 'RRA:AVERAGE:0.5:1:1051200', 'RRA:AVERAGE:0.5:10:210240')
	
	# Update the rdd with new values
	rrdtool.update('%s' % (rrdfile), 'N:%s:%s' % (metric1, metric2) )

# ------------------------------------------------------------------------------
