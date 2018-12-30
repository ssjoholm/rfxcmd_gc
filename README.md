# rfxcmd

DESCRIPTION

RFXcmd is Python script that interfaces the RFX USB devices from RFXcom http://www.rfxcom.com.

All documents and other related to RFXcmd can be found at http://www.rfxcmd.eu

REQUIREMENTS

- Python 2.7, does not work with Python 3.x
- Tested on Raspberry Pi (Debian Squeezy) with Python 2.6
- Tested on Mac OSX 10.8.2 with Python 2.7.2
- Tested with RFXCOM device RFXtrx433-USB (v2.1)

```bash
pip install -r requirements.txt
```

EXAMPLES

```bash
/opt/rfxcmd/rfxcmd.py -l -o /opt/rfxcmd/config.xml -D

/opt/rfxcmd/rfxcmd.py -l -d /dev/cu.usbserial-XXXXXXX -v
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
