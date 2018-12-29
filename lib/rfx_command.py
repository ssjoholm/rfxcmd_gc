#!/usr/bin/python
# coding=UTF-8

# ------------------------------------------------------------------------------
#    
#    RFX_COMMAND.PY
#    
#    2013 Sebastian Sjoholm, sebastian.sjoholm@gmail.com
#
#    All credits for this code goes to the stackoverflow.com and posting;
#    http://stackoverflow.com/questions/16542422/asynchronous-subprocess-with-timeout
#
#    Author: epicbrew
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
#    Website
#    http://code.google.com/p/rfxcmd/
#
#    $Rev: 464 $
#    $Date: 2013-05-01 22:41:36 +0200 (Wed, 01 May 2013) $
#
# ------------------------------------------------------------------------------

# --------------------------------------------------------------------------

import logging
import subprocess
import threading

LOGGER = logging.getLogger('rfxcmd')

class Command(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None

    def run(self, timeout):
        def target():
            LOGGER.debug("Thread started, timeout = %s", str(timeout))
            self.process = subprocess.Popen(self.cmd, shell=True)
            self.process.communicate()
            LOGGER.debug("Return code: %s", str(self.process.returncode))
            LOGGER.debug("Thread finished")
            self.timer.cancel()

        def timer_callback():
            LOGGER.debug("Thread timeout, terminate it")
            if self.process.poll() is None:
                try:
                    self.process.kill()
                except OSError as error:
                    LOGGER.error("Error: %s " % error)
                LOGGER.debug("Thread terminated")
            else:
                LOGGER.debug("Thread not alive")

        thread = threading.Thread(target=target)
        self.timer = threading.Timer(int(timeout), timer_callback)
        self.timer.start()
        thread.start()

# ----------------------------------------------------------------------------
