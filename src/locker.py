#!/usr/bin/env python

import os

LOCK_PREFIX = 'pylocker_'


class Locker:
    def is_locked(self, name):
        if not os.path.exists("/tmp/" + LOCK_PREFIX + name):
            return False

        lock_file = open("/tmp/" + LOCK_PREFIX + name, "r")
        pid = int(lock_file.read())
        lock_file.close()

        try:
            os.kill(pid, 0)
        except OSError:
            return False

        return pid

    def lock(self, name):
        if self.is_locked(name):
            return False

        lock_file = open("/tmp/" + LOCK_PREFIX + name, "w")
        lock_file.write(str(os.getpid()))
        lock_file.close()

        return True

    def unlock(self, name):
        os.remove("/tmp/" + LOCK_PREFIX + name)
