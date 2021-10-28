#!/usr/bin/env python


class Slave:
    def __init__(self, address, logger):
        self.address = address
        self.logger = logger

        self.inputCheck = False
        self.active = False

    def set_input_check(self, check):
        self.inputCheck = check

    def has_input_check(self):
        if not self.is_active():
            return False

        return self.inputCheck

    def set_active(self, active):
        self.active = active

        if not active:
            self.set_input_check(False)

    def is_active(self):
        return self.active
