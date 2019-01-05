#!/usr/bin/python
# coding=UTF-8

# ------------------------------------------------------------------------------
#   
#   RFXCMD.PY
#   
#   Copyright (C) 2012-2013 Sebastian Sjoholm, sebastian.sjoholm@gmail.com
#   
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#   
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#   
#   Version history can be found at 
#   http://code.google.com/p/rfxcmd/wiki/VersionHistory
#
#   $Rev: 464 $
#   $Date: 2013-05-01 22:41:36 +0200 (Wed, 01 May 2013) $
#
#   NOTES
#   
#   RFXCOM is a Trademark of RFSmartLink.
#
# ------------------------------------------------------------------------------
#
#                          Protocol License Agreement                      
#                                                                    
# The RFXtrx protocols are owned by RFXCOM, and are protected under applicable
# copyright laws.
#
# ==============================================================================
# It is only allowed to use this protocol or any part of it for RFXCOM products
# ==============================================================================
#
# The above Protocol License Agreement and the permission notice shall be 
# included in all software using the RFXtrx protocols.
#
# Any use in violation of the foregoing restrictions may subject the user to 
# criminal sanctions under applicable laws, as well as to civil liability for 
# the breach of the terms and conditions of this license.
#
# ------------------------------------------------------------------------------

class rfx_data(dict):

    rfx_cmnd = {
                "00":"Reset the receiver/transceiver. No answer is transmitted!",
                "01":"Not used.",
                "02":"Get Status, return firmware versions and configuration of the interface.",
                "03":"Set mode msg1-msg5, return firmware versions and configuration of the interface.",
                "04":"Enable all receiving modes of the receiver/transceiver.",
                "05":"Enable reporting of undecoded packets.",
                "06":"Save receiving modes of the receiver/transceiver in non-volatile memory.",
                "07":"Not used.",
                "08":"T1 - for internal use by RFXCOM",
                "09":"T2 - for internal use by RFXCOM"
                }

    rfx_packettype = {
                "00":"Interface Control",
                "01":"Interface Message",
                "02":"Receiver/Transmitter Message",
                "03":"Undecoded RF Message",
                "10":"Lighting1",
                "11":"Lighting2",
                "12":"Lighting3",
                "13":"Lighting4",
                "14":"Lighting5",
                "15":"Lighting6",
                "16":"Chime",
                "18":"Curtain1",
                "19":"Blinds1",
                "1A":"RTS",
                "20":"Security1",
                "28":"Camera1",
                "30":"Remote control and IR",
                "40":"Thermostat1",
                "41":"Thermostat2 (Receive not implemented)",
                "42":"Thermostat3",
                "50":"Temperature sensors",
                "51":"Humidity sensors",
                "52":"Temperature and humidity sensors",
                "53":"Barometric sensors",
                "54":"Temperature, humidity and barometric sensors",
                "55":"Rain sensors",
                "56":"Wind sensors",
                "57":"UV sensors",
                "58":"Date/Time sensors",
                "59":"Current sensors",
                "5A":"Energy usage sensors",
                "5B":"Current + Energy sensors",
                "5C":"Power sensors",
                "5D":"Weighting scale",
                "5E":"Gas usage sensors",
                "5F":"Water usage sensors",
                "70":"RFXSensor",
                "71":"RFXMeter",
                "72":"FS20"
                }

    rfx_subtype_01 = {"00":"Response on a mode command"}

    rfx_subtype_01_msg1 = {"50":"310MHz",
                            "51":"315MHz",
                            "52":"433.92MHz (Receiver only)",
                            "53":"433.92MHz (Transceiver)",
                            "55":"868.00MHz",
                            "56":"868.00MHz FSK",
                            "57":"868.30MHz",
                            "58":"868.30MHz FSK",
                            "59":"868.35MHz",
                            "5A":"868.35MHz FSK",
                            "5B":"868.95MHz"}

    rfx_subtype_01_msg3 = {"128":"Undecoded",
                            "64":"RFU",
                            "32":"Byron SX",
                            "16":"RSL",
                            "8":"Lightning4",
                            "4":"FineOffset / Viking",
                            "2":"Rubicson",
                            "1":"AE Blyss"}
                        
    rfx_subtype_01_msg4 = {"128":"Blinds T1/T2/T3/T4",
                            "64":"Blinds T0",
                            "32":"ProGuard",
                            "16":"FS20",
                            "8":"La Crosse",
                            "4":"Hideki / UPM",
                            "2":"AD Lightwave RF",
                            "1":"Mertik"}
                        
    rfx_subtype_01_msg5 = {"128":"Visonic",
                            "64":"ATI",
                            "32":"Oregon Scientific",
                            "16":"Meiantech",
                            "8":"HomeEasy EU",
                            "4":"AC",
                            "2":"ARC",
                            "1":"X10"}

    rfx_subtype_02 = {"00":"Error, receiver did not lock",
                        "01":"Transmitter response"}
                    
    rfx_subtype_02_msg1 = {"00":"ACK, transmit OK",
                            "01":"ACK, but transmit started after 3 seconds delay anyway with RF receive data",
                            "02":"NAK, transmitter did not lock on the requested transmit frequency",
                            "03":"NAK, AC address zero in id1-id4 not allowed"}

    rfx_subtype_03 = {"00":"AC",
                    "01":"ARC",
                    "02":"ATI",
                    "03":"Hideki",
                    "04":"LaCrosse",
                    "05":"AD",
                    "06":"Mertik",
                    "07":"Oregon 1",
                    "08":"Oregon 2",
                    "09":"Oregon 3",
                    "0A":"Proguard",
                    "0B":"Visionic",
                    "0C":"NEC",
                    "0D":"FS20",
                    "0E":"Reserved",
                    "0F":"Blinds",
                    "10":"Rubicson",
                    "11":"AE",
                    "12":"Fineoffset"}

    rfx_subtype_10 = {"00":"X10 Lightning",
                    "01":"ARC",
                    "02":"ELRO AB400D (Flamingo)",
                    "03":"Waveman",
                    "04":"Chacon EMW200",
                    "05":"IMPULS",
                    "06":"RisingSun",
                    "07":"Philips SBC",
                    "08":"Energenie ENER010",
                    "09":"Energenie 5-gang",
                    "0A":"COCO GDR2-2000R"}

    rfx_subtype_10_housecode = {"41":"A",
                                "42":"B",
                                "43":"C",
                                "44":"D",
                                "45":"E",
                                "46":"F",
                                "47":"G",
                                "48":"H",
                                "49":"I",
                                "4A":"J",
                                "4B":"K",
                                "4C":"L",
                                "4D":"M",
                                "4E":"N",
                                "4F":"O",
                                "50":"P"}

    rfx_subtype_10_cmnd = {"00":"Off",
                            "01":"On",
                            "02":"Dim",
                            "03":"Bright",
                            "05":"All/Group Off",
                            "06":"All/Group On",
                            "07":"Chime",
                            "FF":"Illegal cmnd received"}

    rfx_subtype_11 = {"00":"AC",
                        "01":"HomeEasy EU",
                        "02":"Anslut"}
                    
    rfx_subtype_11_cmnd = {"00":"Off",
                            "01":"On",
                            "02":"Set level",
                            "03":"Group Off",
                            "04":"Group On",
                            "05":"Set Group Level"}

    rfx_subtype_11_dimlevel = {"00":"0",
                                "01":"6",
                                "02":"12",
                                "03":"18",
                                "04":"24",
                                "05":"30",
                                "06":"36",
                                "07":"42",
                                "08":"48",
                                "09":"54",
                                "0A":"60",
                                "0B":"66",
                                "0C":"72",
                                "0D":"78",
                                "0E":"84",
                                "0F":"100"}

    rfx_subtype_12 = {"00":"Ikea Koppla"}

    rfx_subtype_12_cmnd = {"00":"Bright",
                            "08":"Dim",
                            "10":"On",
                            "11":"Level 1",
                            "12":"Level 2",
                            "13":"Level 3",
                            "14":"Level 4",
                            "15":"Level 5",
                            "16":"Level 6",
                            "17":"Level 7",
                            "18":"Level 8",
                            "19":"Level 9",
                            "1A":"Off",
                            "1C":"Program"}

    rfx_subtype_13 = {"00":"PT2262"}

    rfx_subtype_14 = {"00":"LightwaveRF, Siemens",
                        "01":"EMW100 GAO/Everflourish",
                        "02":"BBSB new types",
                        "03":"MDREMOTE LED dimmer",
                        "04":"Conrad RSL2",
                        "05":"Livolo",
                        "06":"RGB TRC02",
                        "11":"Chacon Plug 54661"}
    
    # 0x00 LightwaveRF, Siemens
    rfx_subtype_14_cmnd0 = {"00":"Off",
                            "01":"On",
                            "02":"Group off",
                            "03":"Mood1",
                            "04":"Mood2",
                            "05":"Mood3",
                            "06":"Mood4",
                            "07":"Mood5",
                            "08":"Reserved",
                            "09":"Reserved",
                            "0A":"Unlock",
                            "0B":"Lock",
                            "0C":"All lock",
                            "0D":"Close (inline relay)",
                            "0E":"Stop (inline relay)",
                            "0F":"Open (inline relay)",
                            "10":"Set level"}

    # 0x01 EMW100 GAO/Everflourish
    rfx_subtype_14_cmnd1 = {"00":"Off",
                            "01":"On",
                            "02":"Learn"}

    # 0x02 BBSB new types
    rfx_subtype_14_cmnd2 = {"00":"Off",
                            "01":"On",
                            "02":"Group Off",
                            "03":"Group On"}

    # 0x03 MDREMOTE LED dimmer
    rfx_subtype_14_cmnd3 = {"00":"Power",
                            "01":"Light",
                            "02":"Bright",
                            "03":"Dim",
                            "04":"100%",
                            "05":"50%",
                            "06":"25%",
                            "07":"Mode+",
                            "08":"Speed-",
                            "09":"Speed+",
                            "0A":"Mode-"}

    # 0x04 Conrad RSL2
    rfx_subtype_14_cmnd4 = {"00":"Off",
                            "01":"On",
                            "02":"Group Off",
                            "03":"Group On"}
    
    # 0x05 Livolo
    rfx_subtype_14_cmnd5 = {"00":"Group Off",
                            "01":"On/Off dimmer or gang1",
                            "02":"Dim+ or gang2 on/off",
                            "03":"Dim- or gang3 on/off"}
    
    # 0x06 TRC02
    rfx_subtype_14_cmnd6 = {"00":"Off",
                            "01":"On",
                            "02":"Bright",
                            "03":"Dim",
                            "04":"Color+",
                            "05":"Color-"}

    # 0x11 Chacon
    rfx_subtype_14_cmnd11 = {"00":"Off",
                             "01":"On"}

    rfx_subtype_15 = {"00":"Blyss"}

    rfx_subtype_15_groupcode = {"41":"A",
                                "42":"B",
                                "43":"C",
                                "44":"D",
                                "45":"E",
                                "46":"F",
                                "47":"G",
                                "48":"H"}

    rfx_subtype_15_cmnd = {"00":"On",
                            "01":"Off",
                            "02":"group On",
                            "03":"group Off"}
    
    rfx_subtype_16 = {"00":"Byron SX",
                        "01":"Byron MP001",
                        "02":"SelectPlus",
                        "03":"RFU",
                        "04":"Envivo"}
    
    rfx_subtype_16_sound = {"01":"Tubular 3 notes",
                            "03":"Big Ben",
                            "05":"Tubular 2 notes",
                            "09":"Solo",
                            "0D":"Tubular 3 notes",
                            "0E":"Big Ben",
                            "06":"Tubular 2 notes",
                            "02":"Solo"}
    
    rfx_subtype_17 = {"00":"Siemens SF01 - LF959RA50/LF259RB50/LF959RB50"}
    
    rfx_subtype_18 = {"00":"Harrison Curtain"}

    rfx_subtype_19 = {"00":"BlindsT0 / Rollertrol, Hasta new",
                        "01":"BlindsT1 / Hasta old",
                        "02":"BlindsT2 / A-OK RF01",
                        "03":"BlindsT3 / A-OK AC114",
                        "04":"BlindsT4 / Raex YR1326",
                        "05":"BlindsT5 / Media Mount",
                        "06":"BlindsT6 / DC106/Rohrmotor24-RMF/Yooda",
                        "07":"BlindsT7 / Forest"}

    rfx_subtype_1A = {"00":"RTS",
                        "01":"RTS ext (not yet fully implemented)"}
    
    rfx_subtype_1A_cmnd = {"00":"Stop",
                            "01":"Up",
                            "02":"Up+Stop (Set upper limit)",
                            "03":"Down",
                            "04":"Down+Stop (Set lower limit)",
                            "05":"Up+Down (Connect motor)",
                            "07":"Program",
                            "08":"Program > 2 seconds",
                            "09":"Program > 7 seconds",
                            "0A":"Stop > 2 seconds (Set position / Change direction)",
                            "0B":"Stop > 5 seconds (Set middle position)",
                            "0C":"Up+Down > 5 seconds (Change upper position)",
                            "0D":"Erase this RTS remote from RFXtrx",
                            "0E":"Erase all RTS remotes from the RFXtrx"}

    rfx_subtype_20 = {"00":"X10 security door/window sensor",
                        "01":"X10 security motion sensor",
                        "02":"X10 security remote (no alive packets)",
                        "03":"KD101 (no alive packets)",
                        "04":"Visonic PowerCode door/window sensor - Primary contact (with alive packets)",
                        "05":"Visonic PowerCode motion sensor (with alive packets)",
                        "06":"Visonic CodeSecure (no alive packets)",
                        "07":"Visonic PowerCode door/window sensor - auxiliary contact (no alive packets)",
                        "08":"Meiantech/Atlantic/Aidebao",
                        "09":"Alecto SA30 smoke detector"}

    rfx_subtype_20_status = {"00":"Normal",
                            "01":"Normal delayed",
                            "02":"Alarm",
                            "03":"Alarm delayed",
                            "04":"Motion",
                            "05":"No motion",
                            "06":"Panic",
                            "07":"End panic",
                            "08":"IR",
                            "09":"Arm away",
                            "0A":"Arm away delayed",
                            "0B":"Arm home",
                            "0C":"Arm home delayed",
                            "0D":"Disarm",
                            "10":"Light 1 off",
                            "11":"Light 1 on",
                            "12":"Light 2 off",
                            "13":"Light 2 on",
                            "14":"Dark detected",
                            "15":"Light detected",
                            "16":"Batlow (SD18, CO18)",
                            "17":"Pair (KD101)",
                            "80":"Normal + tamper",
                            "81":"Normal delayed + tamper",
                            "82":"Alarm + tamper",
                            "83":"Normal delayed + tamper",
                            "84":"Motion + tamper",
                            "85":"No motion + tamper"}

    rfx_subtype_28 = {"00":"X10 Ninja"}

    rfx_subtype_30 = {"00":"ATI Remote Wonder",
                        "01":"ATI Remote Wonder Plus",
                        "02":"Medion Remote",
                        "03":"X10 PC Remote",
                        "04":"ATI Remote Wonder II (receive only)"}

    rfx_subtype_30_atiremotewonder = {"00":"A",
                                    "01":"B",
                                    "02":"Power",
                                    "03":"TV",
                                    "04":"DVD",
                                    "05":"?",
                                    "06":"Guide",
                                    "07":"Drag",
                                    "08":"VOL+",
                                    "09":"VOL-",
                                    "0A":"MUTE",
                                    "0B":"CHAN+",
                                    "0C":"CHAN-",
                                    "0D":"1",
                                    "0E":"2",
                                    "0F":"3",
                                    "10":"4",
                                    "11":"5",
                                    "12":"6",
                                    "13":"7",
                                    "14":"8",
                                    "15":"9",
                                    "16":"txt",
                                    "17":"0",
                                    "18":"Snapshot ESQ",
                                    "19":"C",
                                    "1A":"^",
                                    "1B":"D",
                                    "1C":"TV/RADIO",
                                    "1D":"<",
                                    "1E":"OK",
                                    "1F":">",
                                    "20":"<-",
                                    "21":"E",
                                    "22":"v",
                                    "23":"F",
                                    "24":"Rewind",
                                    "25":"Play",
                                    "26":"Fast forward",
                                    "27":"Record",
                                    "28":"Stop",
                                    "29":"Pause",
                                    "2C":"TV",
                                    "2D":"VCR",
                                    "2E":"RADIO",
                                    "2F":"TV Preview",
                                    "30":"Channel list",
                                    "31":"Video Desktop",
                                    "32":"red",
                                    "33":"green",
                                    "34":"yellow",
                                    "35":"blue",
                                    "36":"rename TAB",
                                    "37":"Acquire image",
                                    "38":"edit image",
                                    "39":"Full Screen",
                                    "3A":"DVD Audio",
                                    "70":"Cursor-left",
                                    "71":"Cursor-right",
                                    "72":"Cursor-up",
                                    "73":"Cursor-down",
                                    "74":"Cursor-up-left",
                                    "75":"Cursor-up-right",
                                    "76":"Cursor-down-right",
                                    "77":"Cursor-down-left",
                                    "78":"V",
                                    "79":"V-End",
                                    "7C":"X",
                                    "7D":"X-End"}

    rfx_subtype_30_medion = {"00":"Mute",
                            "01":"B",
                            "02":"Power",
                            "03":"TV",
                            "04":"DVD",
                            "05":"Photo",
                            "06":"Music",
                            "07":"Drag",
                            "08":"VOL-",
                            "09":"VOL+",
                            "0A":"MUTE",
                            "0B":"CHAN+",
                            "0C":"CHAN-",
                            "0D":"1",
                            "0E":"2",
                            "0F":"3",
                            "10":"4",
                            "11":"5",
                            "12":"6",
                            "13":"7",
                            "14":"8",
                            "15":"9",
                            "16":"txt",
                            "17":"0",
                            "18":"snapshot ESQ",
                            "19":"DVD MENU",
                            "1A":"^",
                            "1B":"Setup",
                            "1C":"TV/RADIO",
                            "1D":"<",
                            "1E":"OK",
                            "1F":">",
                            "20":"<-",
                            "21":"E",
                            "22":"v",
                            "23":"F",
                            "24":"Rewind",
                            "25":"Play",
                            "26":"Fast forward",
                            "27":"Record",
                            "28":"Stop",
                            "29":"Pause",
                            "2C":"TV",
                            "2D":"VCR",
                            "2E":"RADIO",
                            "2F":"TV Preview",
                            "30":"Channel List",
                            "31":"Video desktop",
                            "32":"red",
                            "33":"green",
                            "34":"yellow",
                            "35":"blue",
                            "36":"rename TAB",
                            "37":"Acquire image",
                            "38":"edit image",
                            "39":"Full screen",
                            "3A":"DVD Audio",
                            "70":"Cursor-left",
                            "71":"Cursor-right",
                            "72":"Cursor-up",
                            "73":"Cursor-down",
                            "74":"Cursor-up-left",
                            "75":"Cursor-up-right",
                            "76":"Cursor-down-right",
                            "77":"Cursor-down-left",
                            "78":"V",
                            "79":"V-End",
                            "7C":"X",
                            "7D":"X-End"}

    rfx_subtype_40 = {"00":"Digimax",
                        "01":"Digimax with short format (no set point)"}

    rfx_subtype_40_status = {"0":"No status available",
                            "1":"Demand",
                            "2":"No demand",
                            "3":"Initializing"}

    rfx_subtype_40_mode = {"0":"Heating",
                            "1":"Cooling"}

    rfx_subtype_41 = {"00":"HE105",
                        "01":"RTS10, RFS10, TLX1206"}

    rfx_subtype_42 = {"00":"Mertik G6R-H4T1",
                        "01":"Mertik G6R-H4TB / G6-H4T / G6R-H4T21-Z22"}

    rfx_subtype_42_cmd00 = {"00":"Off",
                            "01":"On",
                            "02":"Up",
                            "03":"Down",
                            "04":"Run Up",
                            "05":"Run Down",
                            "06":"Stop"}
    
    rfx_subtype_42_cmd01 = {"00":"Off",
                            "01":"On",
                            "02":"Up",
                            "03":"Down",
                            "04":"2nd Off",
                            "05":"2nd On"}

    rfx_subtype_4E = {"00":"Maverick ET-732"}

    rfx_subtype_50 = {"01":"THR128/138, THC138",
                        "02":"THC238/268,THN132,THWR288,THRN122,THN122,AW129/131",
                        "03":"THWR800",
                        "04":"RTHN318",
                        "05":"La Crosse TX2, TX3, TX4, TX17",
                        "06":"TS15C",
                        "07":"Viking 02811",
                        "08":"La Crosse WS2300",
                        "09":"RUBiCSON",
                        "0A":"TFA 30.3133"}

    rfx_subtype_51 = {"01":"LaCrosse TX3",
                        "02":"LaCrosse WS2300"}

    rfx_subtype_51_humstatus = {"00":"Dry",
                                "01":"Comfort",
                                "02":"Normal",
                                "03":"Wet"}

    rfx_subtype_52 = {"01":"THGN122/123, THGN132, THGR122/228/238/268",
                        "02":"THGR810, THGN800",
                        "03":"RTGR328",
                        "04":"THGR328",
                        "05":"WTGR800",
                        "06":"THGR918, THGRN228, THGN50",
                        "07":"TFA TS34C, Cresta",
                        "08":"WT260,WT260H,WT440H,WT450,WT450H",
                        "09":"Viking 02035, 02038",
                        "0A":"Rubicson",
                        "0B":"EW109",
                        "0C":"Imagintronix Soil Sensor",
                        "0D":"Alecto WS1700 and compatibles",
                        "0E":"Alecto WS4500, Auriol H13726, Hama EWS1500, Meteoscan W155/W160,Ventus WS155"}

    rfx_subtype_52_humstatus = {"00":"Dry",
                                "01":"Comfort",
                                "02":"Normal",
                                "03":"Wet"}

    rfx_subtype_53 = {"01":"Reserved for future use"}

    rfx_subtype_54 = {"01":"BTHR918",
                        "02":"BTHR918N, BTHR968"}

    rfx_subtype_54_humstatus = {"00":"Normal",
                                "01":"Comfort",
                                "02":"Dry",
                                "03":"Wet"}

    rfx_subtype_54_forecast = {"00":"No forecast available",
                                "01":"Sunny",
                                "02":"Partly cloudy",
                                "03":"Cloudy",
                                "04":"Rainy"}

    rfx_subtype_55 = {"01":"RGR126/682/918",
                        "02":"PCR800",
                        "03":"TFA",
                        "04":"UPM RG700",
                        "05":"WS2300",
                        "06":"La Crosse TX5"}
                    
    rfx_subtype_56 = {"01":"WTGR800",
                        "02":"WGR800",
                        "03":"STR918, WGR918, WGR928",
                        "04":"TFA",
                        "05":"UPM WDS500",
                        "06":"WS2300",
                        "07":"Alecto WS4500, Auriol H13726, Hama EWS1500, Meteoscan W155/W160, Ventus WS155"}

    rfx_subtype_57 = {"01":"UVN128, UV138",
                        "02":"UVN800",
                        "03":"TFA"}
                    
    rfx_subtype_58 = {"01":"RTGR328N"}

    rfx_subtype_59 = {"01":"CM113, Electrisave, cent-a-meter"}

    rfx_subtype_5A = {"01":"CM119/160",
                        "02":"CM180"}

    rfx_subtype_5B = {"01":"CM180i"}

    rfx_subtype_5C = {"01":"Revolt"}

    rfx_subtype_5D = {"01":"BWR101/102",
                        "02":"GR101"}
    
    rfx_subtype_5E = {"01":"Gas usage sensor"}
    
    rfx_subtype_5F = {"01":"Water usage sensor"}
    
    rfx_subtype_70 = {"00":"RFXSensor temperature",
                        "01":"RFXSensor A/S",
                        "02":"RFXSensor voltage",
                        "03":"RFXSensor message"}
                    
    rfx_subtype_70_msg03 = {"01":"Sensor addresses incremented",
                            "02":"Battery low detected",
                            "81":"No 1-wire device connected",
                            "82":"1-Wire ROM CRC error",
                            "83":"1-Wire device connected is not a DS18B20 or DS2438",
                            "84":"No end of read signal received from 1-Wire device",
                            "85":"1-Wire scratchpad CRC error"}
                    
    rfx_subtype_71 = {"00":"Normal data packet",
                        "01":"New interval time set",
                        "02":"Calibrate value in <count> in usec",
                        "03":"New address set",
                        "04":"Counter value reset within 5 seconds",
                        "0B":"Counter value reset executed",
                        "0C":"Set interval mode within 5 seconds",
                        "0D":"Calibration mode within 5 seconds",
                        "0E":"Set address mode within 5 seconds",
                        "0F":"Identification packet"}
                    
    rfx_subtype_72 = {"00":"FS20",
                        "01":"FHT8V valve",
                        "02":"FHT80 door/window sensor"}
    
    rfx_subtype_7F = {"00":"Raw transmit"}
    
    def __getitem__(self, key): return self[key]
    def keys(self): return self.keys()
