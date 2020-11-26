#!/usr/bin/env python

import io
import fcntl
import sys

# i2c_raw.py
# 2016-02-26
# Public Domain

I2C_SLAVE=0x0703

if sys.hexversion < 0x03000000:
    def _b(x):
        return x
else:
    def _b(x):
        return x.encode('latin-1')

class I2c:
    def __init__(self, bus):
        self.bus = bus

    def write(self, address, data):
        if type(data) is list:
            data = bytearray(data)
        elif type(data) is str:
            data = _b(data)

        bus = io.open("/dev/i2c-" + str(self.bus), "wb", buffering=0)
        fcntl.ioctl(bus, I2C_SLAVE, address)
        bus.write(data)
        bus.close()

    def read(self, address, command, length):
        bus = io.open("/dev/i2c-" + str(self.bus), "rb", buffering=0)
        fcntl.ioctl(bus, I2C_SLAVE, address)
        data = bus.read(length)
        bus.close()

        return data