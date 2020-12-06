#!/usr/bin/env python

import socket
import fcntl
import struct

SEND_PORT = 43000

RECEIVE_RETURN = 0
TYPE_HANDSHAKE = 1


class Network:
    def __init__(self, interface, server_ip, logger):
        self.interface = interface
        self.serverIp = server_ip
        self.logger = logger
        self.receivePort = None
        self.ip = self.get_ip_address()

        self.logger.info("Handshake")
        self.udpServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpServer.bind((self.ip, SEND_PORT))

        self.logger.debug("Connect to Server " + self.serverIp)
        data = self.udpServer.recv(self.send_write_data(TYPE_HANDSHAKE, socket.gethostname()) + 1)
        self.receivePort = ord(data[-1:])

        self.udpServer.close()
        self.udpServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpServer.bind((self.ip, self.receivePort))
        self.receive_receive_return()

    def send_write_data(self, command, data):
        self.logger.debug("Send write data to " + self.serverIp + ":" + str(SEND_PORT))
        self.logger.debug("Command: " + str(command))
        self.logger.debug("Data: " + data)

        send_string = self.get_sent_data(command, data)
        self.udpServer.sendto(send_string, (self.serverIp, SEND_PORT))

        return len(send_string)

    def send_read_data(self, command, data):
        self.logger.debug("Send read data")
        self.logger.debug("Command: " + str(command))
        self.logger.debug("Data: " + data)

        send_string = self.get_sent_data(command, data)
        self.udpServer.sendto(send_string, (self.serverIp, self.receivePort))

        return len(send_string)

    def send_receive_return(self):
        self.logger.debug("Send receive return")
        self.udpServer.sendto(chr(RECEIVE_RETURN), (self.serverIp, self.receivePort))

    def receive_receive_return(self):
        self.logger.debug("Receive receive return")
        self.udpServer.recv(1)
        self.logger.debug("Receive return received")

    def get_sent_data(self, command, data):
        check_sum = command

        for char in self.ip:
            check_sum += ord(char)

        for char in data:
            check_sum += ord(char)

        return self.ip + chr(command) + data + chr(check_sum % 256)

    def receive(self, length):
        return self.udpServer.recv(length)

    def get_ip_address(self):
        return fcntl.ioctl(
            self.udpServer.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', self.interface[:15])
        )[20:24]
