#!/usr/bin/env python

import socket
import fcntl
import struct
from time import sleep

SEND_PORT = 42000
START_PORT = 43000

RECEIVE_RETURN = 0
TYPE_HANDSHAKE = 1


class Network:
    def __init__(self, interface, server_ip, logger):
        self.interface = interface
        self.serverIp = server_ip
        self.logger = logger
        self.receivePort = None

        self.logger.info("Handshake")
        self.udpServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ipBytes = self.get_ip_address()
        self.ip = socket.inet_ntoa(self.ipBytes)
        self.logger.debug("Bind Server on IP " + self.ip + ":" + str(START_PORT))
        self.udpServer.bind((self.ip, START_PORT))

        self.logger.debug("Connect to Server " + self.serverIp)
        data = self.udpServer.recv(self.send_write_data(TYPE_HANDSHAKE, socket.gethostname()) + 1)
        self.receivePort = (ord(data[-2:-1]) << 8) | ord(data[-1:])

        self.udpServer.close()
        self.udpServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger.debug("Bind Server on IP " + self.ip + ":" + str(self.receivePort))
        self.udpServer.bind((self.ip, self.receivePort))

    def send_write_data(self, command, data):
        self.logger.debug("Send write data \"" + data + "\" with command " + str(command) + " to " + self.serverIp + ":" + str(SEND_PORT))

        send_string = self.get_sent_data(command, data)
        self.udpServer.sendto(send_string, (self.serverIp, SEND_PORT))

        return len(send_string)

    def send_read_data(self, command, data):
        self.logger.debug("Send read data \"" + data + "\" with command " + str(command))

        send_string = self.get_sent_data(command, data)
        self.udpServer.sendto(send_string, (self.serverIp, self.receivePort))

        return len(send_string)

    def send_receive_return(self):
        self.logger.debug("Send receive return to " + self.serverIp + ":" + str(self.receivePort))
        sleep(.1)
        self.udpServer.sendto(self.get_sent_data(RECEIVE_RETURN, ''), (self.serverIp, self.receivePort))

    def get_sent_data(self, command, data):
        check_sum = command
        send_data = b''

        for ipByte in self.ipBytes:
            check_sum += ipByte
            send_data += ipByte.to_bytes(1, 'big')

        send_data += command.to_bytes(1, 'big')

        for char in data:
            check_sum += ord(char)
            send_data += ord(char).to_bytes(1, 'big')

        return send_data + (check_sum % 256).to_bytes(1, 'big')

    def receive(self, length):
        return self.udpServer.recv(length)

    def get_ip_address(self):
        return fcntl.ioctl(
            self.udpServer.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', bytes(self.interface[:15], 'utf-8'))
        )[20:24]
