#!/usr/bin/env python

import slave
import threading
from time import sleep

FIRST_CORRUPT_CHECK_ADDRESS = 0
FIRST_ADDRESS = 8
LAST_ADDRESS = 119

TYPE_STATUS = 2
TYPE_NEW_SLAVE = 3
TYPE_SLAVE_HAS_INPUT_CHECK = 4
TYPE_SCAN_BUS = 5
TYPE_ERROR = 127
TYPE_DATA = 255

ERROR_BUS_CORRUPTED = 1

I2C_COMMAND_DATA_CHANGED = 251
I2C_COMMAND_CHANGED_DATA = 255


class HcServer:
    def __init__(self, network, bus, logger):
        self.restartScan = False
        self.scanInProcess = False
        self.slaves = dict()

        for address in range(FIRST_ADDRESS, LAST_ADDRESS + 1):
            self.slaves[address] = slave.Slave(address, logger)

        self.network = network
        self.bus = bus
        self.logger = logger

    def run(self):
        if self.detect_corrupted_bus():
            return

        self.logger.debug("Start UDP thread")
        udp_thread = threading.Thread(target=self.read_udp)
        udp_thread.daemon = True
        udp_thread.start()
        self.logger.debug("UDP thread started")

        self.logger.debug("Start read bus input thread")
        bus_thread = threading.Thread(target=self.read_bus_input)
        bus_thread.daemon = True
        bus_thread.start()
        self.logger.debug("Read bus input thread started")

        self.scan_bus()

        while True:
            sleep(3600)

            if self.detect_corrupted_bus():
                return

    def read_udp(self):
        self.logger.info("Start UDP listener")

        while True:
            try:
                data = self.network.receive(256)
                command = data[0]
                address = data[1] >> 1

                if command == TYPE_SLAVE_HAS_INPUT_CHECK:
                    self.logger.info("Slave %d has input check" % address)
                    self.network.send_receive_return()
                    self.slaves[address].set_input_check(True)
                elif command == TYPE_SCAN_BUS:
                    self.network.send_receive_return()
                    self.scan_bus()
                else:
                    self.logger.info("Data received")
                    self.logger.debug("Address: %d" % address)
                    slave_command = data[2]
                    self.logger.debug("Command: %d" % slave_command)
                    self.logger.debug("Data: %s" % data)
                    # @todo Checksumme pruefen

                    if data[1] & 1 == 1:  # Write
                        self.bus.write(address, slave_command, [i for i in data[3:]])
                        self.network.send_receive_return()
                    else:  # Read
                        self.network.send_read_data(
                            TYPE_DATA,
                            chr(address) + chr(data[2]) + self.bus.read(address, slave_command, data[3])
                        )
            except Exception as exception:
                self.logger.debug(exception)

    def read_bus_input(self):
        self.logger.info("Start bus listener")

        while True:
            for address in range(FIRST_ADDRESS, LAST_ADDRESS + 1):
                if self.slaves[address].has_input_check():
                    try:
                        self.logger.debug("Check changed data. Address: %d" % address)
                        changed_data_length = ord(self.bus.read(address, I2C_COMMAND_DATA_CHANGED, 1))

                        if changed_data_length == 0:
                            continue

                        try:
                            self.logger.debug("Changed Data. Length: %d" % changed_data_length)
                            changed_data = self.bus.read(address, I2C_COMMAND_CHANGED_DATA, changed_data_length)

                            self.network.send_write_data(
                                TYPE_STATUS,
                                chr(address) + chr(I2C_COMMAND_DATA_CHANGED) + changed_data
                            )
                        except Exception as exception:
                            self.logger.debug(exception)
                    except Exception as exception:
                        self.logger.debug(exception)
                        self.logger.warning("Slave %d not found" % address)

                sleep(.002)

    def scan_bus(self):
        self.logger.info("Scan bus")

        if self.scanInProcess:
            self.logger.warning("Scan in process")
            self.restartScan = True
            return None

        self.scanInProcess = True

        for address in range(FIRST_ADDRESS, LAST_ADDRESS + 1):
            if self.restartScan:
                self.logger.warning("Restart scan")
                self.restartScan = False
                address = FIRST_ADDRESS

            try:
                self.logger.debug("Scan address: " + str(address))
                self.bus.read_byte(address)

                if not self.slaves[address].is_active():
                    self.slaves[address].set_active(True)
                    self.network.send_write_data(TYPE_NEW_SLAVE, chr(address))
            except Exception as exception:
                self.logger.debug(exception)
                self.slaves[address].set_active(False)

            sleep(.001)

        self.scanInProcess = False
        self.logger.info("Bus scanned")

    def detect_corrupted_bus(self):
        self.logger.debug("Detect corrupted bus")

        for address in range(FIRST_CORRUPT_CHECK_ADDRESS, FIRST_ADDRESS):
            try:
                self.bus.read_byte(address)
            except Exception:
                return False

        self.logger.warning("Bus is corrupted!")
        self.network.send_read_data(TYPE_ERROR, chr(ERROR_BUS_CORRUPTED))

        return True
