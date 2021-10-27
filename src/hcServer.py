#!/usr/bin/env python

import slave
import threading
from time import sleep

FIRST_ADDRESS = 3
LAST_ADDRESS = 119

TYPE_STATUS = 2
TYPE_NEW_SLAVE = 3
TYPE_SLAVE_HAS_INPUT_CHECK = 4
TYPE_SCAN_BUS = 5
TYPE_DATA = 255

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
        self.logger.debug("Start UDP thread")
        udp_thread = threading.Thread(target=self.read_udp)
        udp_thread.daemon = True
        udp_thread.start()
        self.logger.debug("UDP thread started")

        self.scan_bus()

        while True:
            sleep(3600)

    def read_udp(self):
        self.logger.info("Start UDP listener")

        while True:
            try:
                data = self.network.receive(256)
                command = ord(data[0])
                address = ord(data[1]) >> 1

                if command == TYPE_SLAVE_HAS_INPUT_CHECK:
                    self.logger.debug("Slave %d has input check" % address)
                    self.network.send_receive_return()

                    input_thread = threading.Thread(target=self.read_slave_input, args=(self.slaves[address],))
                    input_thread.daemon = True
                    input_thread.start()
                    self.slaves[address].set_input_thread(input_thread)
                    self.logger.debug("Read bus input thread started")
                elif command == TYPE_SCAN_BUS:
                    self.scan_bus()
                    self.network.send_receive_return()
                else:
                    self.logger.info("Data received")
                    self.logger.debug("Address: " + str(address))
                    slave_command = ord(data[2])
                    self.logger.debug("Command: " + str(slave_command))
                    self.logger.debug("Data: " + data)
                    # @todo Checksumme pruefen

                    if ord(data[1]) & 1 == 1:  # Write
                        self.bus.write(address, slave_command, [ord(i) for i in data[3:]])
                        self.network.send_receive_return()
                    else:  # Read
                        self.network.send_read_data(
                            TYPE_DATA,
                            chr(address) + data[2] + self.bus.read(address, slave_command, ord(data[3]))
                        )
            except Exception:
                pass

    def read_slave_input(self, slave):
        self.logger.info("Start read slave input thread for %d" % slave.address)

        while True:
            if not slave.is_active():
                return

            try:
                self.logger.debug("Check changed data. Address: %d" % slave.address)
                changed_data_length = ord(self.bus.read(slave.address, I2C_COMMAND_DATA_CHANGED, 1))

                try:
                    self.logger.debug("Changed Data. Length: %d" % changed_data_length)
                    changed_data = self.bus.read(slave.address, I2C_COMMAND_CHANGED_DATA, changed_data_length)

                    self.network.send_write_data(
                        TYPE_STATUS,
                        chr(slave.address) + chr(I2C_COMMAND_DATA_CHANGED) + changed_data
                    )
                except:
                    pass
            except:
                self.logger.warning("Slave %d not found" % slave.address)
                slave.set_active(False)

            sleep(.01)

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
            except:
                self.slaves[address].set_active(False)

            sleep(.001)

        self.scanInProcess = False
        self.logger.info("Bus scanned")
