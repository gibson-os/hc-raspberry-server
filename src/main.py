#!/usr/bin/env python

import bus
import network
import hcServer
import logger
import getopt
import sys

interface = 'wlan0:hc'  # 'eth0:hc'
startIp = 254
serverAddress = '192.168.42.1'
busNumber = 3
logLevel = ""

try:
    options, arguments = getopt.getopt(
        sys.argv[1:],
        "i:a:b:s:",
        ["interface=", "start_address=", "bus_number=", "server_address=", "v", "vv", "vvv"]
    )

    for option, argument in options:
        if option in ("-i", "--interface"):
            interface = argument
        elif option in ("-a", "--start_address"):
            startIp = int(argument)
        elif option in ("-s", "--server_address"):
            serverAddress = argument
        elif option in ("-b", "--bus_number"):
            busNumber = int(argument)
        elif option.startswith("--v"):
            logLevel = option
except getopt.GetoptError:
    pass

logger = logger.Logger(logLevel)
logger.info("Start Server on interface " + interface + " with ip " + str(startIp) + " for bus " + str(busNumber))

logger.debug("Create Bus")
bus = bus.Bus(busNumber, logger)
logger.debug("Bus created")

logger.debug("Create network")
network = network.Network(interface, serverAddress, startIp, logger)
logger.debug("Network created")

logger.debug("Create hcServer")
hcServer = hcServer.HcServer(network, bus, logger)
logger.debug("hcServer created")

logger.info("Run hcServer")
hcServer.run()
