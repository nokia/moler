# -*- coding: utf-8 -*-
"""
threaded.network_down_detectors.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A fully-functional connection-observer using socket & threading.
Works on Python 2.7 as well as on 3.6

This is Layer_2 example:
- uses Moler provided external-IO TCP implementation (moler.io.raw.tcp.ThreadedTcp)
- uses full API of connection observer (it has internal concurrency runner)

This example demonstrates multiple connection observers working
on multiple connections.

Shows following concepts:
- multiple observers may observe single connection
- each one is focused on different data (processing decomposition)
- client code may run observers on different connections
- client code may "start" observers in sequence
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import logging
import sys
import os
import threading
import time

from moler.connection import ObservableConnection
from moler.connection_observer import ConnectionObserver
from moler.io.raw import tcp


# ===================== Moler's connection-observer usage ======================
class NetworkToggleDetector(ConnectionObserver):
    def __init__(self, net_ip, detect_pattern, detected_status):
        super(NetworkToggleDetector, self).__init__()
        self.net_ip = net_ip
        self.detect_pattern = detect_pattern
        self.detected_status = detected_status
        self.logger = logging.getLogger('moler.{}'.format(self))

    def data_received(self, data):
        """Awaiting ping output change"""
        if not self.done():
            if self.detect_pattern in data:
                when_detected = time.time()
                self.logger.debug("Network {} {}!".format(self.net_ip,
                                                          self.detected_status))
                self.set_result(result=when_detected)


class NetworkDownDetector(NetworkToggleDetector):
    """
    Awaiting change like:
    64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms
    ping: sendmsg: Network is unreachable
    """
    def __init__(self, net_ip):
        detect_pattern = "Network is unreachable"
        detected_status = "is down"
        super(NetworkDownDetector, self).__init__(net_ip,
                                                  detect_pattern,
                                                  detected_status)


class NetworkUpDetector(NetworkToggleDetector):
    def __init__(self, net_ip):
        detect_pattern = "bytes from {}".format(net_ip)
        detected_status = "is up"
        super(NetworkUpDetector, self).__init__(net_ip,
                                                detect_pattern,
                                                detected_status)


def ping_observing_task(ext_io_connection, ping_ip):
    """
    Here external-IO connection is abstract - we don't know its type.
    What we know is just that it has .moler_connection attribute.
    """
    logger = logging.getLogger('moler.user.app-code')
    conn_addr = str(ext_io_connection)

    # Layer 2 of Moler's usage (ext_io_connection + runner):
    # 3. create observers on Moler's connection
    net_down_detector = NetworkDownDetector(ping_ip)
    net_down_detector.connection = ext_io_connection.moler_connection
    net_up_detector = NetworkUpDetector(ping_ip)
    net_up_detector.connection = ext_io_connection.moler_connection

    info = '{} on {} using {}'.format(ping_ip, conn_addr, net_down_detector)
    logger.debug('observe ' + info)

    # 4. start observer (nonblocking, using as future)
    net_down_detector.start()  # should be started before we open connection
    # to not loose first data on connection

    with ext_io_connection:
        # 5. await that observer to complete
        net_down_time = net_down_detector.await_done(timeout=10)
        timestamp = time.strftime("%H:%M:%S", time.localtime(net_down_time))
        logger.debug('Network {} is down from {}'.format(ping_ip, timestamp))

        # 6. call next observer (blocking till completes)
        info = '{} on {} using {}'.format(ping_ip, conn_addr, net_up_detector)
        logger.debug('observe ' + info)
        # using as synchronous function (so we want verb to express action)
        detect_network_up = net_up_detector
        net_up_time = detect_network_up()
        timestamp = time.strftime("%H:%M:%S", time.localtime(net_up_time))
        logger.debug('Network {} is back "up" from {}'.format(ping_ip, timestamp))


# ==============================================================================
def main(connections2observe4ip):
    # Starting the clients
    connections = []
    for address, ping_ip in connections2observe4ip:
        host, port = address
        # 1. create Moler's connection that knows encoding
        decoder = lambda data: data.decode("utf-8")
        moler_conn = ObservableConnection(decoder=decoder)
        # 2. create external-IO connection gluing to Moler's connection
        conn_logger_name = 'threaded.tcp-connection({}:{})'.format(*address)
        conn_logger = logging.getLogger(conn_logger_name)
        tcp_connection = tcp.ThreadedTcp(moler_connection=moler_conn,
                                         port=port, host=host,
                                         logger=conn_logger)
        client_thread = threading.Thread(target=ping_observing_task,
                                         args=(tcp_connection, ping_ip))
        client_thread.start()
        connections.append(client_thread)
    # await observers job to be done
    for client_thread in connections:
        client_thread.join()


# ==============================================================================
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))  # allow finding modules in examples/

if __name__ == '__main__':
    from threaded_ping_server import start_ping_servers, stop_ping_servers

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s |%(name)-40s |%(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )
    connections2observe4ip = [(('localhost', 5671), '10.0.2.15'),
                              (('localhost', 5672), '10.0.2.16')]
    servers = start_ping_servers(connections2observe4ip)
    main(connections2observe4ip)
    stop_ping_servers(servers)

'''
LOG OUTPUT

14:10:44 |threaded.ping.tcp-server(5671)           |Ping Sim started at tcp://localhost:5671
14:10:44 |threaded.ping.tcp-server(5672)           |Ping Sim started at tcp://localhost:5672
14:10:44 |moler.user.app-code                      |observe 10.0.2.15 on tcp://localhost:5671 using NetworkDownDetector(id:47689008)
14:10:44 |moler.runner.thread-pool                 |starting NetworkDownDetector(id:47689008)
14:10:44 |moler.user.app-code                      |observe 10.0.2.16 on tcp://localhost:5672 using NetworkDownDetector(id:47752080)
14:10:44 |moler.runner.thread-pool                 |starting NetworkDownDetector(id:47752080)
14:10:44 |threaded.tcp-connection(localhost:5671)  |connecting to tcp://localhost:5671
14:10:44 |threaded.tcp-connection(localhost:5672)  |connecting to tcp://localhost:5672
14:10:44 |threaded.tcp-connection(localhost:5671)  |connection tcp://localhost:5671 is open
14:10:44 |threaded.ping.tcp-server(5671 -> 58889)  |connection accepted - client at tcp://127.0.0.1:58889
14:10:44 |threaded.tcp-connection(localhost:5671)  |< b'\n'
14:10:44 |moler.runner.thread-pool                 |awaiting NetworkDownDetector(id:47689008)
14:10:44 |threaded.tcp-connection(localhost:5672)  |connection tcp://localhost:5672 is open
14:10:44 |moler.runner.thread-pool                 |awaiting NetworkDownDetector(id:47752080)
14:10:44 |threaded.ping.tcp-server(5672 -> 58890)  |connection accepted - client at tcp://127.0.0.1:58890
14:10:44 |threaded.tcp-connection(localhost:5672)  |< b'\n'
14:10:45 |threaded.tcp-connection(localhost:5671)  |< b'greg@debian:~$ ping 10.0.2.15\n'
14:10:45 |threaded.tcp-connection(localhost:5672)  |< b'greg@debian:~$ ping 10.0.2.16\n'
14:10:46 |threaded.tcp-connection(localhost:5671)  |< b'PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.\n'
14:10:46 |threaded.tcp-connection(localhost:5672)  |< b'PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.\n'
14:10:47 |threaded.tcp-connection(localhost:5671)  |< b'64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms\n'
14:10:47 |threaded.tcp-connection(localhost:5672)  |< b'64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms\n'
14:10:48 |threaded.tcp-connection(localhost:5671)  |< b'64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms\n'
14:10:48 |threaded.tcp-connection(localhost:5672)  |< b'64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms\n'
14:10:49 |threaded.tcp-connection(localhost:5671)  |< b'64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms\n'
14:10:49 |threaded.tcp-connection(localhost:5672)  |< b'64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms\n'
14:10:50 |threaded.tcp-connection(localhost:5671)  |< b'ping: sendmsg: Network is unreachable\n'
14:10:50 |moler.NetworkDownDetector(id:47689008)   |Network 10.0.2.15 is down!
14:10:50 |threaded.tcp-connection(localhost:5672)  |< b'ping: sendmsg: Network is unreachable\n'
14:10:50 |moler.NetworkDownDetector(id:47752080)   |Network 10.0.2.16 is down!
14:10:50 |moler.runner.thread-pool                 |shutting down
14:10:50 |moler.runner.thread-pool                 |NetworkDownDetector(id:47689008) returned 1519823450.4585001
14:10:50 |moler.user.app-code                      |Network 10.0.2.15 is down from 14:10:50
14:10:50 |moler.user.app-code                      |observe 10.0.2.15 on tcp://localhost:5671 using NetworkUpDetector(id:47689568)
14:10:50 |moler.runner.thread-pool                 |starting NetworkUpDetector(id:47689568)
14:10:50 |moler.runner.thread-pool                 |awaiting NetworkUpDetector(id:47689568)
14:10:50 |moler.runner.thread-pool                 |shutting down
14:10:50 |moler.runner.thread-pool                 |NetworkDownDetector(id:47752080) returned 1519823450.4620001
14:10:50 |moler.user.app-code                      |Network 10.0.2.16 is down from 14:10:50
14:10:50 |moler.user.app-code                      |observe 10.0.2.16 on tcp://localhost:5672 using NetworkUpDetector(id:47752472)
14:10:50 |moler.runner.thread-pool                 |starting NetworkUpDetector(id:47752472)
14:10:50 |moler.runner.thread-pool                 |awaiting NetworkUpDetector(id:47752472)
14:10:51 |threaded.tcp-connection(localhost:5671)  |< b'ping: sendmsg: Network is unreachable\n'
14:10:51 |threaded.tcp-connection(localhost:5672)  |< b'ping: sendmsg: Network is unreachable\n'
14:10:52 |threaded.tcp-connection(localhost:5671)  |< b'ping: sendmsg: Network is unreachable\n'
14:10:52 |threaded.tcp-connection(localhost:5672)  |< b'ping: sendmsg: Network is unreachable\n'
14:10:53 |threaded.tcp-connection(localhost:5671)  |< b'64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms\n'
14:10:53 |moler.NetworkUpDetector(id:47689568)     |Network 10.0.2.15 is up!
14:10:53 |threaded.tcp-connection(localhost:5672)  |< b'64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms\n'
14:10:53 |moler.NetworkUpDetector(id:47752472)     |Network 10.0.2.16 is up!
14:10:53 |moler.runner.thread-pool                 |shutting down
14:10:53 |moler.runner.thread-pool                 |NetworkUpDetector(id:47689568) returned 1519823453.459
14:10:53 |moler.user.app-code                      |Network 10.0.2.15 is back "up" from 14:10:53
14:10:53 |moler.runner.thread-pool                 |shutting down
14:10:53 |moler.runner.thread-pool                 |NetworkUpDetector(id:47752472) returned 1519823453.4625
14:10:53 |moler.user.app-code                      |Network 10.0.2.16 is back "up" from 14:10:53
14:10:53 |threaded.tcp-connection(localhost:5671)  |connection tcp://localhost:5671 is closed
14:10:53 |threaded.tcp-connection(localhost:5672)  |connection tcp://localhost:5672 is closed
14:10:53 |threaded.ping.tcp-server(5671)           |Ping Sim: ... bye
14:10:53 |threaded.ping.tcp-server(5672)           |Ping Sim: ... bye
14:10:55 |threaded.ping.tcp-server(5671 -> 58889)  |Connection closed
14:10:55 |threaded.ping.tcp-server(5672 -> 58890)  |Connection closed
'''
