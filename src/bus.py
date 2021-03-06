#!/usr/bin/python

import smbus
from time import sleep


class Bus:
    def __init__(self, bus_number, logger):
        self.busBlocked = False
        self.busNumber = bus_number
        self.logger = logger

    def write(self, address, command, data):
        bus = self.get_smbus()

        try:
            if len(data) == 1:
                self.logger.debug("Write byte data %d to address %d with command %d" % (data[0], address, command))
                bus.write_byte_data(address, command, data[0])
            else:
                self.logger.debug("Write block data with length %d to address %d with command %d" % (len(data), address, command))
                # self.logger.debug("Data: " + str(data[0]))
                bus.write_block_data(address, command, data)
        except Exception as exception:
            self.close_smbus(bus)
            raise exception

        self.close_smbus(bus)

    def read(self, address, command, length):
        self.logger.debug("Read %d bytes from address %d with command %d" % (length, address, command))

        string = ''
        bus = self.get_smbus()

        try:
            for byte in bus.read_i2c_block_data(address, command, length):
                string += chr(byte)
        except Exception as exception:
            self.close_smbus(bus)
            raise exception

        self.close_smbus(bus)
        self.logger.debug("Data: " + string)

        return string

    def read_byte(self, address):
        self.logger.debug("Read byte from address " + str(address))

        bus = self.get_smbus()

        try:
            byte = bus.read_byte(address)
        except Exception as exception:
            self.close_smbus(bus)
            raise exception

        self.close_smbus(bus)

        return byte

    def get_smbus(self):
        self.wait_for_free()
        self.busBlocked = True

        self.logger.debug("Create SMBus: " + str(self.busNumber))
        bus = smbus.SMBus(self.busNumber)
        self.logger.debug("SMBus created")

        return bus

    def close_smbus(self, bus):
        self.logger.debug("Close SMBus")
        sleep(.001)
        bus.close()
        sleep(.001)
        self.busBlocked = False
        self.logger.debug("SMBus closed")

    def wait_for_free(self):
        self.logger.debug("Wait for free bus")

        while self.busBlocked:
            pass

        self.logger.debug("Bus free")
