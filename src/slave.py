#!/usr/bin/env python


class Slave:
    def __init__(self, address, logger):
        self.address = address
        self.logger = logger

        self.inputThread = None
        self.active = False

    def set_input_thread(self, thread):
        self.inputThread = thread

    def get_input_thread(self):
        return self.inputThread

    def set_active(self, active):
        self.active = active

        if not active:
            if self.inputThread is not None:
                self.inputThread.stop()
                self.inputThread = None

    def is_active(self):
        return self.active
