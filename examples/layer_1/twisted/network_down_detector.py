# -*- coding: utf-8 -*-
"""
twisted.network_down_detector.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A fully-functional connection-observer using twisted.
Works on Python 2.7 as well as on 3.6

This example demonstrates basic concept of connection observer - entity
that is fully responsible for:
- observing data coming from connection till it catches what it is waiting for
- parsing that data to have "caught event" stored in expected form
- storing that result internally for later retrieval

Please note that this example is LAYER-1 usage which means:
- observer can't run by its own, must be fed with data (passive observer)
- observer can't be awaited, must be queried for status before asking for data
Another words - low level manual combining of all the pieces.
"""
from twisted.internet.protocol import Protocol, Factory, ClientFactory
from twisted.internet import reactor, task
from twisted.internet.defer import Deferred

import logging
import sys
import time
from functools import partial

from moler.connection_observer import ConnectionObserver
from moler.connection import ObservableConnection

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

ping_output = '''
greg@debian:~$ ping 10.0.2.15
PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.
64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms
64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms
64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms
ping: sendmsg: Network is unreachable
ping: sendmsg: Network is unreachable
ping: sendmsg: Network is unreachable
64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms
64 bytes from 10.0.2.15: icmp_req=8 ttl=64 time=0.056 ms
'''


class PingSimTcpServer(Protocol):
    def __init__(self):
        self.logger = logging.getLogger('twisted.ping.tcp-server')
        self.ping_lines = ping_output.splitlines(True)

    def connectionMade(self):
        client_info = 'client at tcp://{}:{}'.format(*self.transport.client)
        self.logger.debug('connection accepted - ' + client_info)
        self.send_ping_line()

    def connectionLost(self, reason):
        self.logger.debug("Connection closed")

    def send_ping_line(self):
        if self.ping_lines:
            ping_line = self.ping_lines.pop(0)
            data = ping_line.encode(encoding='utf-8')
            self.transport.write(data)
            # simulate delay between ping lines
            reactor.callLater(1, self.send_ping_line)


def start_ping_sim_server(server_address):
    """Run server simulating ping command output, this is one-shot server"""
    logger = logging.getLogger('twisted.ping.tcp-server')
    host, port = server_address
    factory = Factory()
    factory.protocol = PingSimTcpServer
    reactor.listenTCP(port, factory)

    logger.debug("Ping Sim started at tcp://{}:{}".format(*server_address))
    logger.debug("WARNING - I'll be tired too much just after first client!")


class TcpConnection(Protocol):
    def __init__(self, forward_data):
        self.forward_data = forward_data
        self.logger = logging.getLogger('twisted.tcp-connection')

    def connectionMade(self):
        conn_info = 'tcp://{}:{}'.format(*self.transport.realAddress)
        self.logger.debug('... connected to ' + conn_info)

    def connectionLost(self, reason):
        self.logger.debug("... closed")

    def dataReceived(self, data):
        self.logger.debug('<<< {!r}'.format(data))
        self.forward_data(data)


def start_tcp_connection(address, forward_data):
    host, port = address
    factory = ClientFactory()
    factory.protocol=partial(TcpConnection, forward_data)
    reactor.connectTCP(host, port, factory)


def main(reactor, address):
    # Starting the server
    start_ping_sim_server(address)
    # Starting the client
    processing_done_deferred = ping_observing_task(address)
    return processing_done_deferred


# ===================== Moler's connection-observer usage ======================

class NetworkDownDetector(ConnectionObserver):
    def __init__(self):
        super(NetworkDownDetector, self).__init__()
        self.logger = logging.getLogger('moler.net-down-detector')

    def data_received(self, data):
        if not self.done():
            if "Network is unreachable" in data:  # observer operates on strings
                when_network_down_detected = time.time()
                self.logger.debug("Network is down!")
                self.set_result(result=when_network_down_detected)


def ping_observing_task(address):
    logger = logging.getLogger('moler.user.app-code')
    observer_done = Deferred()

    # Lowest layer of Moler's usage (you manually glue all elements):
    # 1. create observer
    net_down_detector = NetworkDownDetector()
    # 2. ObservableConnection is a proxy-glue between observer (speaks str)
    #                                   and asyncio-connection (speaks bytes)
    moler_conn = ObservableConnection(decoder=lambda data: data.decode("utf-8"))
    # 3a. glue from proxy to observer
    moler_conn.subscribe(net_down_detector.data_received)

    logger.debug('waiting for data to observe')

    def feed_moler(connection_data):
        # 3b. glue to proxy from external-IO (asyncio tcp client connection)
        #    (client has to pass it's received data into Moler's connection)
        moler_conn.data_received(connection_data)
        # 4. Moler's client code must manually check status of observer ...
        if net_down_detector.done():
            # 5. ... to know when it can ask for result
            net_down_time = net_down_detector.result()
            timestamp = time.strftime("%H:%M:%S",
                                      time.localtime(net_down_time))
            logger.debug('Network is down from {}'.format(timestamp))
            observer_done.callback(None)  # break tcp client and server

    start_tcp_connection(address, feed_moler)
    return observer_done


# ==============================================================================
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s |%(name)25s |%(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )
    address = ('localhost', 5670)
    task.react(main, argv=[address])
