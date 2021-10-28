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
                self.logger.info("Write byte data %d to address %d with command %d" % (data[0], address, command))
                self.write_byte_data(bus, address, command, data[0])
            else:
                self.logger.info("Write block data with length %d to address %d with command %d" % (len(data), address, command))
                # self.logger.debug("Data: " + str(data[0]))
                self.write_block_data(bus, address, command, data)
        except Exception as exception:
            self.close_smbus(bus)
            raise exception

        self.close_smbus(bus)

    def read(self, address, command, length):
        self.logger.info("Read %d bytes from address %d with command %d" % (length, address, command))

        string = ''
        bus = self.get_smbus()

        try:
            for byte in self.read_i2c_block_data(bus, address, command, length):
                string += chr(byte)
        except Exception as exception:
            self.close_smbus(bus)
            raise exception

        self.close_smbus(bus)
        self.logger.debug("Data: " + string)

        return string

    def read_byte(self, address):
        self.logger.info("Read byte from address " + str(address))

        bus = self.get_smbus()

        try:
            byte = bus.read_byte_from_bus(bus, address)
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
        bus.close()
        sleep(.001)
        self.busBlocked = False
        self.logger.debug("SMBus closed")

    def wait_for_free(self):
        self.logger.debug("Wait for free bus")

        while self.busBlocked:
            pass

        self.logger.debug("Bus free")

    def write_byte_data(self, bus, address, command, byte, retry=0):
        try:
            bus.write_byte_data(address, command, byte)
        except Exception as exception:
            if retry == 9:
                raise exception

            self.write_byte_data(bus, address, command, byte, retry + 1)

    def write_block_data(self, bus, address, command, data, retry=0):
        try:
            bus.write_block_data(address, command, data)
        except Exception as exception:
            if retry == 9:
                raise exception

            self.write_block_data(bus, address, command, data, retry + 1)

    def read_i2c_block_data(self, bus, address, command, length, retry=0):
        try:
            bus.read_i2c_block_data(address, command, length)
        except Exception as exception:
            if retry == 9:
                raise exception

            self.read_i2c_block_data(bus, address, command, length, retry + 1)

    def read_byte_from_bus(self, bus, address, retry=0):
        try:
            bus.read_byte(address)
        except Exception as exception:
            if retry == 9:
                raise exception

            self.read_byte_from_bus(bus, address, retry + 1)
