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

        for address in range(FIRST_ADDRESS, LAST_ADDRESS+1):
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

        self.logger.debug("Start read bus input thread")
        bus_thread = threading.Thread(target=self.read_bus_input)
        bus_thread.daemon = True
        bus_thread.start()
        self.logger.debug("Read bus input thread started")

        self.scan_bus()

        while True:
            sleep(3600)

    def read_udp(self):
        self.logger.info("Start UDP listener")

        while True:
            try:
                data = self.network.receive(256)
                command = ord(data[0])

                if command == TYPE_SLAVE_HAS_INPUT_CHECK:
                    self.logger.info("Slave has input check")
                    address = ord(data[1])
                    self.logger.debug("Address: " + str(address))
                    self.slaves[address].set_input_check(True)
                    self.network.send_receive_return()
                elif command == TYPE_SCAN_BUS:
                    self.scan_bus()
                    self.network.send_receive_return()
                else:
                    self.logger.info("Data received")
                    address = ord(data[1]) >> 1
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

    def read_bus_input(self):
        self.logger.info("Start bus listener")

        while True:
            for address in range(FIRST_ADDRESS, LAST_ADDRESS+1):
                if self.slaves[address].has_input_check():
                    changed_data_length = 0

                    try:
                        self.logger.debug("Check changed data. Address: " + str(address))
                        changed_data_length = ord(self.bus.read(address, I2C_COMMAND_DATA_CHANGED, 1))
                    except:
                        self.logger.warning("Slave not found")
                        self.slaves[address].set_active(False)

                    if changed_data_length:
                        try:
                            self.logger.debug("Changed Data. Length: " + str(changed_data_length))
                            changed_data = self.bus.read(address, I2C_COMMAND_CHANGED_DATA, changed_data_length)

                            self.network.send_write_data(
                                TYPE_STATUS,
                                chr(address) + chr(I2C_COMMAND_DATA_CHANGED) + changed_data
                            )
                        except:
                            pass

                sleep(.001)

    def scan_bus(self):
        self.logger.info("Scan bus")

        if self.scanInProcess:
            self.logger.warning("Scan in process")
            self.restartScan = True
            return None

        self.scanInProcess = True

        for address in range(FIRST_ADDRESS, LAST_ADDRESS+1):
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
