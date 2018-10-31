# -*- coding: utf-8 -*-
"""
asyncio_runner_with_raw_functions.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A fully-functional connection-observer using configured concurrency variant.

This is Layer_3 example:
- shows configuration phase and usage phase
  - configure named connections via config file
- uses Moler provided TCP connection implementation
- usage hides implementation variant via factories
- variant is known only during backend configuration phase
- uses connection observer with asyncio runner

This example demonstrates multiple connection observers working
on multiple connections.

Shows following concepts:
- multiple observers may observe single connection
- each one is focused on different data (processing decomposition)
- client code may run observers on different connections
- client code may "start" observers in sequence

Shows how to use connection observers inside raw 'def xxx()' functions and
how to mix it with threads.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import logging
import select
import socket
import sys
import threading
import time
from contextlib import closing
import asyncio

from moler.connection import ObservableConnection
from moler.connection_observer import ConnectionObserver
from moler.io.raw import tcp
from moler.connection import get_connection, ConnectionFactory
from moler.asyncio_runner import AsyncioRunner, AsyncioInThreadRunner

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


def ping_sim_tcp_server(server_port, ping_ip, client, address):
    # asyncio's policy:
    # You must either create an event loop explicitly for each thread
    asyncio.set_event_loop(asyncio.new_event_loop())

    _, client_port = address
    logger = logging.getLogger('threaded.ping.tcp-server({} -> {})'.format(server_port,
                                                                           client_port))
    logger.debug('connection accepted - client at tcp://{}:{}'.format(*address))
    ping_out = ping_output.replace("10.0.2.15", ping_ip)
    ping_lines = ping_out.splitlines(True)
    with closing(client):
        for ping_line in ping_lines:
            data = ping_line.encode(encoding='utf-8')
            try:
                client.sendall(data)
            except socket.error:  # client is gone
                break
            time.sleep(1)  # simulate delay between ping lines
    logger.info('Connection closed')


def server_loop(server_port, server_socket, ping_ip, done_event):
    # asyncio's policy:
    # You must either create an event loop explicitly for each thread
    asyncio.set_event_loop(asyncio.new_event_loop())

    logger = logging.getLogger('threaded.ping.tcp-server({})'.format(server_port))
    while not done_event.is_set():
        # without select we can't break loop from outside (via done_event)
        # since .accept() is blocking
        read_sockets, _, _ = select.select([server_socket], [], [], 0.1)
        if not read_sockets:
            continue
        client_socket, client_addr = server_socket.accept()
        client_socket.setblocking(1)
        client_thread = threading.Thread(target=ping_sim_tcp_server,
                                         args=(server_port, ping_ip,
                                               client_socket, client_addr))
        client_thread.start()
    logger.debug("Ping Sim: ... bye")


def start_ping_sim_server(server_address, ping_ip):
    """Run server simulating ping command output, this is one-shot server"""
    _, server_port = server_address
    logger = logging.getLogger('threaded.ping.tcp-server({})'.format(server_port))
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(server_address)
    server_socket.listen(1)
    logger.debug("Ping Sim started at tcp://{}:{}".format(*server_address))
    done_event = threading.Event()
    server_thread = threading.Thread(target=server_loop,
                                     args=(server_port, server_socket, ping_ip,
                                           done_event))
    server_thread.start()
    return server_thread, done_event


def main(connections2observe4ip):
    # Starting the servers
    servers = []
    for address, _, ping_ip in connections2observe4ip:
        # simulate pinging given IP
        server_thread, server_done = start_ping_sim_server(address, ping_ip)
        servers.append((server_thread, server_done))
    # Starting the clients
    connections = []
    for _, connection_name, ping_ip in connections2observe4ip:
        # ------------------------------------------------------------------
        # This front-end code hides all details of connection.
        # We just use its name - such name should be meaningful for user.
        # like: "main_dns_server", "backup_ntp_server", ...
        # Another words, all we want here is stg like:
        # "give me connection to main_dns_server"
        # ------------------------------------------------------------------
        tcp_connection = get_connection(name=connection_name)
        tcp_connection.moler_connection.name = connection_name
        client_thread = threading.Thread(target=ping_observing_task,
                                         args=(tcp_connection, ping_ip))
        client_thread.start()
        connections.append(client_thread)
    # await observers job to be done
    for client_thread in connections:
        client_thread.join()
    # stop servers
    for server_thread, server_done in servers:
        server_done.set()
        server_thread.join()


# ===================== Moler's connection-observer usage ======================
class NetworkToggleDetector(ConnectionObserver):
    def __init__(self, net_ip, detect_pattern, detected_status,
                 connection=None, runner=None):
        super(NetworkToggleDetector, self).__init__(connection=connection,
                                                    runner=runner)
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
    def __init__(self, net_ip, connection=None, runner=None):
        detect_pattern = "Network is unreachable"
        detected_status = "is down"
        super(NetworkDownDetector, self).__init__(net_ip,
                                                  detect_pattern,
                                                  detected_status,
                                                  connection=connection,
                                                  runner=runner)


class NetworkUpDetector(NetworkToggleDetector):
    def __init__(self, net_ip, connection=None, runner=None):
        detect_pattern = "bytes from {}".format(net_ip)
        detected_status = "is up"
        super(NetworkUpDetector, self).__init__(net_ip,
                                                detect_pattern,
                                                detected_status,
                                                connection=connection,
                                                runner=runner)


def ping_observing_task(ext_io_connection, ping_ip):
    """
    Here external-IO connection is abstract - we don't know its type.
    What we know is just that it has .moler_connection attribute.
    """
    # asyncio's policy:
    # You must either create an event loop explicitly for each thread
    asyncio.set_event_loop(asyncio.new_event_loop())

    logger = logging.getLogger('moler.user.app-code')
    conn_addr = str(ext_io_connection)

    # Layer 2 of Moler's usage (ext_io_connection + runner):
    # 3. create observers on Moler's connection
    net_down_detector = NetworkDownDetector(ping_ip,
                                            connection=ext_io_connection.moler_connection,
                                            runner=AsyncioInThreadRunner())
                                            # runner=AsyncioRunner())
    net_up_detector = NetworkUpDetector(ping_ip,
                                        connection=ext_io_connection.moler_connection,
                                        runner=AsyncioInThreadRunner())
                                        # runner=AsyncioRunner())

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
if __name__ == '__main__':
    import os
    from moler.config import load_config
    # -------------------------------------------------------------------
    # Configure moler connections (backend code)
    # 1) configure variant by YAML config file
    # 2) ver.2 - configure named connections by YAML config file
    load_config(config=os.path.join(os.path.dirname(__file__), "..", "named_connections.yml"))

    # 3) take default class used to realize tcp-threaded-connection
    # -------------------------------------------------------------------

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s |%(name)-45s | %(threadName)12s |%(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )
    connections2observe4ip = [(('localhost', 5671), 'net_1', '10.0.2.15'),
                              (('localhost', 5672), 'net_2', '10.0.2.16')]
    main(connections2observe4ip)
'''
LOG OUTPUT

20:21:32 |threaded.ping.tcp-server(5671)           |Ping Sim started at tcp://localhost:5671
20:21:32 |asyncio                                  |Using selector: SelectSelector
20:21:32 |threaded.ping.tcp-server(5672)           |Ping Sim started at tcp://localhost:5672
20:21:32 |asyncio                                  |Using selector: SelectSelector
20:21:32 |asyncio                                  |Using selector: SelectSelector
20:21:32 |asyncio                                  |Using selector: SelectSelector
20:21:32 |moler.runner.asyncio                     |created
20:21:32 |moler.runner.asyncio                     |created
20:21:32 |moler.user.app-code                      |observe 10.0.2.16 on tcp://localhost:5672 using NetworkDownDetector(id:3096828)
20:21:32 |moler.runner.asyncio                     |go background: NetworkDownDetector(id:3096828, using ObservableConnection(id:3096438)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096550>>])
20:21:32 |moler.runner.asyncio                     |subscribing for data NetworkDownDetector(id:3096828, using ObservableConnection(id:3096438)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096550>>])
20:21:32 |moler.runner.asyncio                     |created
20:21:32 |moler.runner.asyncio                     |created
20:21:32 |moler.user.app-code                      |observe 10.0.2.15 on tcp://localhost:5671 using NetworkDownDetector(id:30969e8)
20:21:32 |moler.runner.asyncio                     |go background: NetworkDownDetector(id:30969e8, using ObservableConnection(id:3096400)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096160>>])
20:21:32 |moler.runner.asyncio                     |subscribing for data NetworkDownDetector(id:30969e8, using ObservableConnection(id:3096400)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096160>>])
20:21:32 |moler.runner.asyncio                     |go foreground: NetworkDownDetector(id:3096828, using ObservableConnection(id:3096438)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096550>>]) - await max. 10 [sec]
20:21:32 |moler.runner.asyncio                     |START OF feed(NetworkDownDetector(id:3096828))
20:21:32 |asyncio                                  |Using selector: SelectSelector
20:21:32 |asyncio                                  |Using selector: SelectSelector
20:21:32 |moler.runner.asyncio                     |go foreground: NetworkDownDetector(id:30969e8, using ObservableConnection(id:3096400)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096160>>]) - await max. 10 [sec]
20:21:32 |moler.runner.asyncio                     |START OF feed(NetworkDownDetector(id:30969e8))
20:21:32 |threaded.ping.tcp-server(5671 -> 51735)  |connection accepted - client at tcp://127.0.0.1:51735
20:21:32 |moler.connection.net_1                   |b'\n'
20:21:32 |threaded.ping.tcp-server(5672 -> 51734)  |connection accepted - client at tcp://127.0.0.1:51734
20:21:32 |moler.connection.net_2                   |b'\n'
20:21:33 |moler.connection.net_1                   |b'greg@debian:~$ ping 10.0.2.15\n'
20:21:33 |moler.connection.net_2                   |b'greg@debian:~$ ping 10.0.2.16\n'
20:21:34 |moler.connection.net_1                   |b'PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.\n'
20:21:34 |moler.connection.net_2                   |b'PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.\n'
20:21:35 |moler.connection.net_2                   |b'64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms\n'
20:21:35 |moler.connection.net_1                   |b'64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms\n'
20:21:36 |moler.connection.net_2                   |b'64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms\n'
20:21:36 |moler.connection.net_1                   |b'64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms\n'
20:21:37 |moler.connection.net_2                   |b'64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms\n'
20:21:37 |moler.connection.net_1                   |b'64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms\n'
20:21:38 |moler.connection.net_2                   |b'ping: sendmsg: Network is unreachable\n'
20:21:38 |moler.NetworkDownDetector(id:3096828)    |Network 10.0.2.16 is down!
20:21:38 |moler.runner.asyncio                     |done & unsubscribing NetworkDownDetector(id:3096828, using ObservableConnection(id:3096438)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096550>>])
20:21:38 |moler.runner.asyncio                     |returning result NetworkDownDetector(id:3096828)
20:21:38 |moler.runner.asyncio                     |END   OF feed(NetworkDownDetector(id:3096828))
20:21:38 |moler.runner.asyncio                     |NetworkDownDetector(id:3096828) returned 1535134898.7966645
20:21:38 |moler.user.app-code                      |Network 10.0.2.16 is down from 20:21:38
20:21:38 |moler.user.app-code                      |observe 10.0.2.16 on tcp://localhost:5672 using NetworkUpDetector(id:30968d0)
20:21:38 |moler.connection.net_1                   |b'ping: sendmsg: Network is unreachable\n'
20:21:38 |moler.NetworkDownDetector(id:30969e8)    |Network 10.0.2.15 is down!
20:21:38 |moler.runner.asyncio                     |go background: NetworkUpDetector(id:30968d0, using ObservableConnection(id:3096438)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096550>>])
20:21:38 |moler.runner.asyncio                     |subscribing for data NetworkUpDetector(id:30968d0, using ObservableConnection(id:3096438)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096550>>])
20:21:38 |moler.runner.asyncio                     |go foreground: NetworkUpDetector(id:30968d0, using ObservableConnection(id:3096438)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096550>>]) - await max. None [sec]
20:21:38 |moler.runner.asyncio                     |START OF feed(NetworkUpDetector(id:30968d0))
20:21:38 |moler.runner.asyncio                     |done & unsubscribing NetworkDownDetector(id:30969e8, using ObservableConnection(id:3096400)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096160>>])
20:21:38 |moler.runner.asyncio                     |returning result NetworkDownDetector(id:30969e8)
20:21:38 |moler.runner.asyncio                     |END   OF feed(NetworkDownDetector(id:30969e8))
20:21:38 |moler.runner.asyncio                     |NetworkDownDetector(id:30969e8) returned 1535134898.7996647
20:21:38 |moler.user.app-code                      |Network 10.0.2.15 is down from 20:21:38
20:21:38 |moler.user.app-code                      |observe 10.0.2.15 on tcp://localhost:5671 using NetworkUpDetector(id:3096ba8)
20:21:38 |moler.runner.asyncio                     |go background: NetworkUpDetector(id:3096ba8, using ObservableConnection(id:3096400)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096160>>])
20:21:38 |moler.runner.asyncio                     |subscribing for data NetworkUpDetector(id:3096ba8, using ObservableConnection(id:3096400)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096160>>])
20:21:38 |moler.runner.asyncio                     |go foreground: NetworkUpDetector(id:3096ba8, using ObservableConnection(id:3096400)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096160>>]) - await max. None [sec]
20:21:38 |moler.runner.asyncio                     |START OF feed(NetworkUpDetector(id:3096ba8))
20:21:39 |moler.connection.net_2                   |b'ping: sendmsg: Network is unreachable\n'
20:21:39 |moler.connection.net_1                   |b'ping: sendmsg: Network is unreachable\n'
20:21:40 |moler.connection.net_2                   |b'ping: sendmsg: Network is unreachable\n'
20:21:40 |moler.connection.net_1                   |b'ping: sendmsg: Network is unreachable\n'
20:21:41 |moler.connection.net_2                   |b'64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms\n'
20:21:41 |moler.NetworkUpDetector(id:30968d0)      |Network 10.0.2.16 is up!
20:21:41 |moler.connection.net_1                   |b'64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms\n'
20:21:41 |moler.NetworkUpDetector(id:3096ba8)      |Network 10.0.2.15 is up!
20:21:41 |moler.runner.asyncio                     |done & unsubscribing NetworkUpDetector(id:3096ba8, using ObservableConnection(id:3096400)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096160>>])
20:21:41 |moler.runner.asyncio                     |returning result NetworkUpDetector(id:3096ba8)
20:21:41 |moler.runner.asyncio                     |END   OF feed(NetworkUpDetector(id:3096ba8))
20:21:41 |moler.runner.asyncio                     |NetworkUpDetector(id:3096ba8) returned 1535134901.7991648
20:21:41 |moler.user.app-code                      |Network 10.0.2.15 is back "up" from 20:21:41
20:21:41 |moler.runner.asyncio                     |done & unsubscribing NetworkUpDetector(id:30968d0, using ObservableConnection(id:3096438)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096550>>])
20:21:41 |moler.runner.asyncio                     |returning result NetworkUpDetector(id:30968d0)
20:21:41 |moler.runner.asyncio                     |END   OF feed(NetworkUpDetector(id:30968d0))
20:21:41 |moler.runner.asyncio                     |NetworkUpDetector(id:30968d0) returned 1535134901.7966645
20:21:41 |moler.user.app-code                      |Network 10.0.2.16 is back "up" from 20:21:41
20:21:41 |threaded.ping.tcp-server(5671)           |Ping Sim: ... bye
20:21:42 |threaded.ping.tcp-server(5672)           |Ping Sim: ... bye
20:21:43 |threaded.ping.tcp-server(5672 -> 51734)  |Connection closed
20:21:43 |threaded.ping.tcp-server(5671 -> 51735)  |Connection closed
20:21:43 |moler.runner.asyncio                     |shutting down
20:21:43 |moler.runner.asyncio                     |shutting down
20:21:43 |moler.runner.asyncio                     |shutting down
20:21:43 |moler.runner.asyncio                     |shutting down
'''
