#!/bin/bash
# rfxcmd daemon
# chkconfig: 345 20 80
# description: rfxcmd daemon
# processname: rfxcmd.py

##############################################################################
#
# Note, you might need to change the parameters below, the current settings
# are for default setup.
#
##############################################################################

DAEMON_PATH="/opt/rfxcmd/"
SERIAL_DEVICE="/dev/rfxcom"
CONFIG_FILE="/opt/rfxcmd/config.xml"

DAEMON=rfxcmd.py
DAEMONOPTS="-l -o $CONFIG_FILE $OTHER_SWITCH"

NAME=rfxcmd
DESC="rfxcmd daemon startup script"
PIDFILE=/var/run/$NAME.pid
SCRIPTNAME=/etc/init.d/$NAME

case "$1" in
start)
	printf "%-50s" "Starting $NAME..."
    # Check if PID exists, and if process is active
	if [ -f $PIDFILE ]; then
    	PID=`cat $PIDFILE`
        if [ -z "`ps axf | grep ${PID} | grep -v grep`" ]; then
			# Process not active remove PID file
            rm -f $PIDFILE
		else
			printf "%s\n" "Process already started..."
			exit 1
        fi
	fi

	$DAEMON_PATH$DAEMON $DAEMONOPTS
        
	# Check process
	PID=`cat $PIDFILE`
	if [ -f $PID ]; then
    	printf "%s\n" "Fail"
	else
    	printf "%s\n" "Ok"
	fi
;;
status)
    printf "%-50s" "Checking $NAME..."
    if [ -f $PIDFILE ]; then
    	PID=`cat $PIDFILE`
        if [ -z "`ps axf | grep ${PID} | grep -v grep`" ]; then
        	printf "%s\n" "Process dead but pidfile exists"
		else
        	echo "Running"
		fi
	else
	    printf "%s\n" "Service not running"
    fi
;;
stop)
    printf "%-50s" "Stopping $NAME"
	PID=`cat $PIDFILE`
	cd $DAEMON_PATH
    if [ -f $PIDFILE ]; then
    	kill -HUP $PID
        printf "%s\n" "Ok"
        rm -f $PIDFILE
	else
    	printf "%s\n" "pidfile not found"
	fi
;;

restart)
  	$0 stop
  	$0 start
;;

*)
        echo "Usage: $0 {status|start|stop|restart}"
        exit 1
esac
