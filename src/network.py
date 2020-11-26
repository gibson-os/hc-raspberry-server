#!/usr/bin/env python

import fcntl
import struct
import socket

RECEIVE_PORT = 7363
SEND_PORT = 7339

RECEIVE_RETURN = 0
TYPE_HANDSHAKE = 1


class Network:
    def __init__(self, interface, serverIp, ip, logger):
        self.interface = interface
        self.serverIp = serverIp
        self.ip = ip
        self.logger = logger
        self.udpServer = None
        self.udpReceiveReturn = None

        self.subnet = serverIp[0:serverIp.rindex('.')] + '.'

        self.create_server()
        self.set_ip(ip)

        self.udpSender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSender.settimeout(1)

        self.handshake()

    def handshake(self):
        self.logger.info("Handshake")
        self.logger.debug("Connect to Server " + self.serverIp)
        data = self.udpServer.recv(self.send_write_data(TYPE_HANDSHAKE, socket.gethostname()) + 1)
        self.send_receive_return()
        self.set_ip(ord(data[-1:]))

    def set_ip(self, ip):
        self.logger.debug("Set IP " + self.subnet + str(ip))
        self.ip = ip
        bin_ip = socket.inet_aton(self.subnet + str(ip))
        ifreq = struct.pack('16sH2s4s8s', self.interface, socket.AF_INET, '\x00'*2, bin_ip, '\x00'*8)
        fcntl.ioctl(self.udpServer, 0x8916, ifreq)
        self.logger.debug("IP set")

        self.close_server()
        self.open_server()

    def close_server(self):
        self.logger.debug("Close server")
        self.udpServer.close()
        self.udpReceiveReturn.close()
        self.logger.debug("Server closed")

    def create_server(self):
        self.logger.debug("Create server")
        self.udpServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpReceiveReturn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger.debug("Server created")

    def open_server(self):
        self.create_server()

        self.logger.debug("Set timeout")
        self.udpServer.settimeout(10)
        self.udpReceiveReturn.settimeout(1)

        self.logger.debug("Bind server to " + self.subnet + str(self.ip))
        self.udpServer.bind((self.subnet + str(self.ip), RECEIVE_PORT))
        self.udpReceiveReturn.bind((self.subnet + str(self.ip), SEND_PORT))
        self.logger.debug("Server opened")

    def send_write_data(self, command, data):
        self.logger.debug("Send write data")
        self.logger.debug("Command: " + str(command))
        self.logger.debug("Data: " + data)

        send_string = self.get_sent_data(command, data)
        self.udpSender.sendto(send_string, (self.serverIp, SEND_PORT))

        return len(send_string)

    def send_read_data(self, command, data):
        self.logger.debug("Send read data")
        self.logger.debug("Command: " + str(command))
        self.logger.debug("Data: " + data)

        send_string = self.get_sent_data(command, data)
        self.udpServer.sendto(send_string, (self.serverIp, RECEIVE_PORT))

        return len(send_string)

    def send_receive_return(self):
        self.logger.debug("Send receive return")
        self.udpServer.sendto(chr(self.ip) + chr(RECEIVE_RETURN), (self.serverIp, RECEIVE_PORT))

    def receive_receive_return(self):
        self.logger.debug("Receive receive return")
        self.udpReceiveReturn.recv(1)
        self.logger.debug("Receive return received")

    def get_sent_data(self, command, data):
        check_sum = self.ip + command

        for char in data:
            check_sum += ord(char)

        return chr(self.ip) + chr(command) + data + chr(check_sum % 256)

    def receive(self, length):
        return self.udpServer.recv(length)
