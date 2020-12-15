#!/usr/bin/env python

import bus
import network
import hcServer
import locker
import logger
import getopt
import sys
import os

interface = 'wlan0'  # 'eth0'
serverAddress = '192.168.27.1'
busNumber = 3
logLevel = ""
force = False

try:
    options, arguments = getopt.getopt(
        sys.argv[1:],
        "i:a:b:s:f",
        ["interface=", "bus_number=", "server_address=", "force", "v", "vv", "vvv"]
    )

    for option, argument in options:
        if option in ("-i", "--interface"):
            interface = argument
        elif option in ("-s", "--server_address"):
            serverAddress = argument
        elif option in ("-b", "--bus_number"):
            busNumber = int(argument)
        elif option in ("--v", "--vv", "--vvv"):
            logLevel = option
        elif option in ("-f", "--force"):
            force = True
except getopt.GetoptError:
    pass

logger = logger.Logger(logLevel)

lock_name = 'hcServer'
locker = locker.Locker()
locked_pid = locker.is_locked(lock_name)

if locked_pid:
    logger.info("Server already runs!")

    if not force:
        exit(1)

    logger.info("Force start Server!")
    os.kill(locked_pid, 9)

logger.info("Start Server on interface " + interface + " for bus " + str(busNumber))
locker.lock(lock_name)

logger.debug("Create Bus")
bus = bus.Bus(busNumber, logger)
logger.debug("Bus created")

logger.debug("Create network")
network = network.Network(interface, serverAddress, logger)
logger.debug("Network created")

logger.debug("Create hcServer")
hcServer = hcServer.HcServer(network, bus, logger)
logger.debug("hcServer created")

logger.info("Run hcServer")
hcServer.run()
