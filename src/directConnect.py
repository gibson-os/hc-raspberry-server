#!/usr/bin/env python

import sqlite3


class DirectConnect:
    def __init__(self, logger):
        self.logger = logger

        self.database = sqlite3.connect("sirectConnects.db")
        cursor = self.database.cursor()
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table' AND tbl_name='direct_connect'")

        if cursor.rowcount == 0:
            cursor.execute("CREATE TABLE direct_connect(id INTEGER PRIMARY KEY, repeat INTEGER)")
            cursor.execute("CREATE TABLE direct_connect_step(id INTEGER PRIMARY KEY, direct_connect_id INTEGER, slave_address INTEGER, order INTEGER, data VARCHAR(20), runtime INTEGER)")
            cursor.execute("CREATE TABLE direct_connect_trigger(id INTEGER PRIMARY KEY, direct_connect_id INTEGER, slave_address INTEGER, data VARCHAR(20))")
            self.database.commit()