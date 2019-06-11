#!/bin/bash

DEVICE="${1}"

# 0x01 - Interface Message
./rfxcmd.py -d "${DEVICE}" -x 1401FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF >/dev/null 2>&1; RET=$?
if [ $RET -ne 0 ]; then
    exit 1
fi
./rfxcmd.py -d "${DEVICE}" -x 0D01FFFFFFFFFFFFFFFFFFFFFFFF >/dev/null 2>&1; RET=$?
if [ $RET -ne 0 ]; then
    exit 1
fi
./rfxcmd.py -d "${DEVICE}" -x 1301FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF >/dev/null 2>&1; RET=$?
if [ $RET -ne 1 ]; then
    exit 1
fi

# 0x02 - Receiver/Transmitter Message
./rfxcmd.py -d "${DEVICE}" -x 0402FFFFFFFF >/dev/null 2>&1; RET=$?
if [ $RET -ne 0 ]; then
    exit 1
fi
./rfxcmd.py -d "${DEVICE}" -x 1302FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF >/dev/null 2>&1; RET=$?
if [ $RET -ne 1 ]; then
    exit 1
fi
