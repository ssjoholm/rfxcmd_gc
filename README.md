# rfxcmd

[![Build Status](https://travis-ci.org/nbeguier/rfxcmd.svg?branch=master)](https://travis-ci.org/nbeguier/rfxcmd) [![Python 3.4|3.7](https://img.shields.io/badge/python-3.4|3.7-green.svg)](https://www.python.org/) [![License](https://img.shields.io/badge/Licence-GPLv3-blue.svg)](https://github.com/nbeguier/rfxcmd/blob/master/doc/COPYING)

DESCRIPTION

RFXcmd is Python script that interfaces the RFX USB devices from RFXcom http://www.rfxcom.com.

All documents and other related to RFXcmd can be found at http://www.rfxcmd.eu

REQUIREMENTS

- Python 3.x
- Tested on Raspberry Pi (Debian Jessie 8.11) with Python 3.4
- Tested on Mac OSX 10.8.2 with Python 3.7
- Tested with RFXCOM device RFXtrx433-USB (v2.1)

```bash
pip3 install -r requirements.txt
```

EXAMPLES

```bash
# Listen from configuration file, in debug mode (-D)
/opt/rfxcmd/rfxcmd.py -l -o /opt/rfxcmd/config.xml -D

# Listen from configuration file, in verbose mode (-v)
/opt/rfxcmd/rfxcmd.py -l -o /opt/rfxcmd/config.xml -D

# Listen from device (-d) in json output
/opt/rfxcmd/rfxcmd.py -l -d /dev/cu.usbserial-XXXXXXX

# Listen from device (-d) in csv output
/opt/rfxcmd/rfxcmd.py -l -d /dev/cu.usbserial-XXXXXXX --csv

# Simulate one incoming data message : 0D01FFFFFFFFFFFFFFFFFFFFFFFF
/opt/rfxcmd/rfxcmd.py -d /dev/cu.usbserial-XXXXXXX -x 0D01FFFFFFFFFFFFFFFFFFFFFFFF

# Send one message to RFX device : 0D01FFFFFFFFFFFFFFFFFFFFFFFF
/opt/rfxcmd/rfxcmd.py -d /dev/cu.usbserial-XXXXXXX -s 0D01FFFFFFFFFFFFFFFFFFFFFFFF

# Get RFX device status (-f) in verbose mode (-v)
/opt/rfxcmd/rfxcmd.py -d /dev/cu.usbserial-XXXXXXX -f -v

# RFXPROTO: List all protocols
/opt/rfxcmd/rfxproto.py -d /dev/cu.usbserial-XXXXXXX -l -D

# RFXSEND: (Need RFXCMD to be running), send raw message 1401FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
/opt/rfxcmd/rfxsend.py -r 1401FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

# RFXSEND: simulate to send send raw message 1401FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
/opt/rfxcmd/rfxsend.py --simulate -r 1401FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

```

```bash
$ cat /var/log/output.log
{"packettype_id": "56", "timestamp": "2018-12-29 16:30:46", "subtype": "TFA", "rawcmd": "10560405991600430001000B0020002059", "seqnbr": "05", "packettype": "Wind sensors", "metadata": {"wind_gust": 1.1, "battery": 9, "wind_direction": 67, "wind_chill": "3.2", "signal_level": 5, "wind_average_speed": 0.1, "id": "9916", "temperature": "3.2"}}
{"packettype_id": "20", "timestamp": "2018-12-30 10:50:49", "subtype": "0x0A", "rawcmd": "08200A00C180830659", "seqnbr": "00", "packettype": "Security1", "metadata": {"battery": 9, "status": "Panic", "id": "C18083", "signal_level": 5}}

$ cat /var/log/output.log | jq .
{
  "packettype_id": "56",
  "timestamp": "2018-12-29 16:30:46",
  "subtype": "TFA",
  "rawcmd": "10560405991600430001000B0020002059",
  "seqnbr": "05",
  "packettype": "Wind sensors",
  "metadata": {
    "wind_gust": 1.1,
    "battery": 9,
    "wind_direction": 67,
    "wind_chill": "3.2",
    "signal_level": 5,
    "wind_average_speed": 0.1,
    "id": "9916",
    "temperature": "3.2"
  }
}
{
  "packettype_id": "20",
  "timestamp": "2018-12-30 10:50:49",
  "subtype": "0x0A",
  "rawcmd": "08200A00C180830659",
  "seqnbr": "00",
  "packettype": "Security1",
  "metadata": {
    "battery": 9,
    "status": "Panic",
    "id": "C18083",
    "signal_level": 5
  }
```


THANKS

Thanks to following users who have helped with testing, patches, ideas, bug reports, and so on (in no special order). Anders, Dimitri, Patrik, Ludwig, Jean-Michel, Jean-Baptiste, Robert, Fabien, Bert, George, Jean-Francois, Mark, Frederic, Matthew, Arno, Jean-Louis, Christophe, Fredrik, Neil, Pierre-Yves and to RFXCOM for their support.

NOTES

RFXCOM is a Trademark of RFSmartLink.

COPYRIGHT

Copyright (C) 2012-2015 Sebastian Sjoholm. This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.
