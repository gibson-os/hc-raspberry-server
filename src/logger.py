#!/usr/bin/env python

class Logger:
    def __init__(self, level):
        self.level = level

    def debug(self, message):
        if self.level.startswith("--vvv"):
            print '\033[44m', message, '\033[0m'

    def warning(self, message):
        if self.level.startswith("--vv"):
            print '\033[101m', message, '\033[0m'

    def info(self, message):
        if self.level.startswith("--v"):
            print '\033[0m', message
