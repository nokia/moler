# -*- coding: utf-8 -*-
"""
network_down_detectors_on_tcp_conn_v2.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A fully-functional connection-observer using configured concurrency variant.

This is Layer_3 example:
- shows configuration phase and usage phase
  - configuration using plugin system
- uses Moler provided TCP connection implementation
- usage hides implementation variant via factories
- variant is known only during backend configuration phase
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

from moler.threaded_moler_connection import ThreadedMolerConnection
from moler.io.raw import tcp
from moler.connection_factory import get_connection, ConnectionFactory

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))  # allow finding modules in examples/

from network_toggle_observers import NetworkDownDetector, NetworkUpDetector


# ===================== Moler's connection-observer usage ======================


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

    with ext_io_connection.open():
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
        # ------------------------------------------------------------------
        # This front-end code hides parallelism variant
        # used to read data from connection.
        # We don't care if it is TCP connection based on threads or asyncio.
        # All we want here is "any TCP connection towards given host/port".
        # "any" means here: TCP variant as configured on backend.
        # ------------------------------------------------------------------
        tcp_connection = get_connection(io_type='tcp', host=host, port=port)
        client_thread = threading.Thread(target=ping_observing_task,
                                         args=(tcp_connection, ping_ip))
        client_thread.start()
        connections.append(client_thread)
    # await observers job to be done
    for client_thread in connections:
        client_thread.join()


# ==============================================================================
if __name__ == '__main__':
    from threaded_ping_server import start_ping_servers, stop_ping_servers
    from moler import config
    # -------------------------------------------------------------------
    # Configure moler connections (backend code)
    # ver.1 - configure via Python code

    # configure parallelism variant of connection
    config.connections.set_default_variant(io_type='tcp', variant='threaded')

    # configure class used to realize tcp-threaded-connection
    # (default one tcp.ThreadedTcp has no logger)
    # This constitutes plugin system - you can exchange connection implementation

    def tcp_thd_conn(port, host='localhost', name=None):
        moler_conn = ThreadedMolerConnection(decoder=lambda data: data.decode("utf-8"))
        conn_logger_name = 'threaded.tcp-connection({}:{})'.format(host, port)
        conn_logger = logging.getLogger(conn_logger_name)
        io_conn = tcp.ThreadedTcp(moler_connection=moler_conn,
                                  port=port, host=host, logger=conn_logger)
        return io_conn

    ConnectionFactory.register_construction(io_type="tcp",
                                            variant="threaded",
                                            constructor=tcp_thd_conn)
    # -------------------------------------------------------------------

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

15:44:46 |threaded.ping.tcp-server(5671)           |Ping Sim started at tcp://localhost:5671
15:44:46 |threaded.ping.tcp-server(5672)           |Ping Sim started at tcp://localhost:5672
15:44:46 |moler.runner.thread-pool                 |created
15:44:46 |moler.runner.thread-pool                 |created own executor <concurrent.futures.thread.ThreadPoolExecutor object at 0x0000000002DFC278>
15:44:46 |moler.runner.thread-pool                 |created
15:44:46 |moler.runner.thread-pool                 |created
15:44:46 |moler.runner.thread-pool                 |created own executor <concurrent.futures.thread.ThreadPoolExecutor object at 0x0000000002DFC6A0>
15:44:46 |moler.runner.thread-pool                 |created own executor <concurrent.futures.thread.ThreadPoolExecutor object at 0x0000000002DFC7B8>
15:44:46 |moler.runner.thread-pool                 |created
15:44:46 |moler.user.app-code                      |observe 10.0.2.15 on tcp://localhost:5671 using NetworkDownDetector(id:2dfc198)
15:44:46 |moler.runner.thread-pool                 |created own executor <concurrent.futures.thread.ThreadPoolExecutor object at 0x0000000002DFCAC8>
15:44:46 |moler.runner.thread-pool                 |go background: NetworkDownDetector(id:2dfc198, using ThreadedMolerConnection(id:2de4e80)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC048>>])
15:44:46 |moler.user.app-code                      |observe 10.0.2.16 on tcp://localhost:5672 using NetworkDownDetector(id:2dfc668)
15:44:46 |moler.runner.thread-pool                 |subscribing for data NetworkDownDetector(id:2dfc198, using ThreadedMolerConnection(id:2de4e80)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC048>>])
15:44:46 |moler.runner.thread-pool                 |go background: NetworkDownDetector(id:2dfc668, using ThreadedMolerConnection(id:2dfc358)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC400>>])
15:44:46 |moler.runner.thread-pool                 |subscribing for data NetworkDownDetector(id:2dfc668, using ThreadedMolerConnection(id:2dfc358)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC400>>])
15:44:46 |threaded.tcp-connection(localhost:5671)  |connecting to tcp://localhost:5671
15:44:46 |threaded.tcp-connection(localhost:5672)  |connecting to tcp://localhost:5672
15:44:46 |threaded.tcp-connection(localhost:5671)  |connection tcp://localhost:5671 is open
15:44:46 |threaded.tcp-connection(localhost:5672)  |connection tcp://localhost:5672 is open
15:44:46 |moler.runner.thread-pool                 |go foreground: NetworkDownDetector(id:2dfc668, using ThreadedMolerConnection(id:2dfc358)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC400>>]) - await max. 10 [sec]
15:44:46 |threaded.ping.tcp-server(5671 -> 60274)  |connection accepted - client at tcp://127.0.0.1:60274
15:44:46 |threaded.tcp-connection(localhost:5671)  |< b'\n'
15:44:46 |moler.connection.2de4e80                 |

15:44:46 |moler.runner.thread-pool                 |go foreground: NetworkDownDetector(id:2dfc198, using ThreadedMolerConnection(id:2de4e80)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC048>>]) - await max. 10 [sec]
15:44:46 |threaded.ping.tcp-server(5672 -> 60275)  |connection accepted - client at tcp://127.0.0.1:60275
15:44:46 |threaded.tcp-connection(localhost:5672)  |< b'\n'
15:44:46 |moler.connection.2dfc358                 |

15:44:47 |threaded.tcp-connection(localhost:5671)  |< b'greg@debian:~$ ping 10.0.2.15\n'
15:44:47 |moler.connection.2de4e80                 |greg@debian:~$ ping 10.0.2.15

15:44:47 |threaded.tcp-connection(localhost:5672)  |< b'greg@debian:~$ ping 10.0.2.16\n'
15:44:47 |moler.connection.2dfc358                 |greg@debian:~$ ping 10.0.2.16

15:44:48 |threaded.tcp-connection(localhost:5671)  |< b'PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.\n'
15:44:48 |moler.connection.2de4e80                 |PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.

15:44:48 |threaded.tcp-connection(localhost:5672)  |< b'PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.\n'
15:44:48 |moler.connection.2dfc358                 |PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.

15:44:49 |threaded.tcp-connection(localhost:5671)  |< b'64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms\n'
15:44:49 |moler.connection.2de4e80                 |64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms

15:44:49 |threaded.tcp-connection(localhost:5672)  |< b'64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms\n'
15:44:49 |moler.connection.2dfc358                 |64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms

15:44:50 |threaded.tcp-connection(localhost:5671)  |< b'64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms\n'
15:44:50 |moler.connection.2de4e80                 |64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms

15:44:50 |threaded.tcp-connection(localhost:5672)  |< b'64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms\n'
15:44:50 |moler.connection.2dfc358                 |64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms

15:44:51 |threaded.tcp-connection(localhost:5671)  |< b'64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms\n'
15:44:51 |moler.connection.2de4e80                 |64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms

15:44:51 |threaded.tcp-connection(localhost:5672)  |< b'64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms\n'
15:44:51 |moler.connection.2dfc358                 |64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms

15:44:52 |threaded.tcp-connection(localhost:5671)  |< b'ping: sendmsg: Network is unreachable\n'
15:44:52 |moler.connection.2de4e80                 |ping: sendmsg: Network is unreachable

15:44:52 |moler.NetworkDownDetector(id:2dfc198)    |Network 10.0.2.15 is down!
15:44:52 |threaded.tcp-connection(localhost:5672)  |< b'ping: sendmsg: Network is unreachable\n'
15:44:52 |moler.connection.2dfc358                 |ping: sendmsg: Network is unreachable

15:44:52 |moler.NetworkDownDetector(id:2dfc668)    |Network 10.0.2.16 is down!
15:44:52 |moler.runner.thread-pool                 |done & unsubscribing NetworkDownDetector(id:2dfc198, using ThreadedMolerConnection(id:2de4e80)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC048>>])
15:44:52 |moler.runner.thread-pool                 |returning result NetworkDownDetector(id:2dfc198)
15:44:52 |moler.runner.thread-pool                 |shutting down
15:44:52 |moler.runner.thread-pool                 |NetworkDownDetector(id:2dfc198) returned 1528983892.6403692
15:44:52 |moler.user.app-code                      |Network 10.0.2.15 is down from 15:44:52
15:44:52 |moler.user.app-code                      |observe 10.0.2.15 on tcp://localhost:5671 using NetworkUpDetector(id:2dfc748)
15:44:52 |moler.runner.thread-pool                 |go background: NetworkUpDetector(id:2dfc748, using ThreadedMolerConnection(id:2de4e80)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC048>>])
15:44:52 |moler.runner.thread-pool                 |subscribing for data NetworkUpDetector(id:2dfc748, using ThreadedMolerConnection(id:2de4e80)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC048>>])
15:44:52 |moler.runner.thread-pool                 |done & unsubscribing NetworkDownDetector(id:2dfc668, using ThreadedMolerConnection(id:2dfc358)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC400>>])
15:44:52 |moler.runner.thread-pool                 |returning result NetworkDownDetector(id:2dfc668)
15:44:52 |moler.runner.thread-pool                 |shutting down
15:44:52 |moler.runner.thread-pool                 |go foreground: NetworkUpDetector(id:2dfc748, using ThreadedMolerConnection(id:2de4e80)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC048>>]) - await max. None [sec]
15:44:52 |moler.runner.thread-pool                 |NetworkDownDetector(id:2dfc668) returned 1528983892.642369
15:44:52 |moler.user.app-code                      |Network 10.0.2.16 is down from 15:44:52
15:44:52 |moler.user.app-code                      |observe 10.0.2.16 on tcp://localhost:5672 using NetworkUpDetector(id:2dfc940)
15:44:52 |moler.runner.thread-pool                 |go background: NetworkUpDetector(id:2dfc940, using ThreadedMolerConnection(id:2dfc358)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC400>>])
15:44:52 |moler.runner.thread-pool                 |subscribing for data NetworkUpDetector(id:2dfc940, using ThreadedMolerConnection(id:2dfc358)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC400>>])
15:44:52 |moler.runner.thread-pool                 |go foreground: NetworkUpDetector(id:2dfc940, using ThreadedMolerConnection(id:2dfc358)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC400>>]) - await max. None [sec]
15:44:53 |threaded.tcp-connection(localhost:5671)  |< b'ping: sendmsg: Network is unreachable\n'
15:44:53 |moler.connection.2de4e80                 |ping: sendmsg: Network is unreachable

15:44:53 |threaded.tcp-connection(localhost:5672)  |< b'ping: sendmsg: Network is unreachable\n'
15:44:53 |moler.connection.2dfc358                 |ping: sendmsg: Network is unreachable

15:44:54 |threaded.tcp-connection(localhost:5671)  |< b'ping: sendmsg: Network is unreachable\n'
15:44:54 |moler.connection.2de4e80                 |ping: sendmsg: Network is unreachable

15:44:54 |threaded.tcp-connection(localhost:5672)  |< b'ping: sendmsg: Network is unreachable\n'
15:44:54 |moler.connection.2dfc358                 |ping: sendmsg: Network is unreachable

15:44:55 |threaded.tcp-connection(localhost:5671)  |< b'64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms\n'
15:44:55 |moler.connection.2de4e80                 |64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms

15:44:55 |moler.NetworkUpDetector(id:2dfc748)      |Network 10.0.2.15 is up!
15:44:55 |threaded.tcp-connection(localhost:5672)  |< b'64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms\n'
15:44:55 |moler.connection.2dfc358                 |64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms

15:44:55 |moler.NetworkUpDetector(id:2dfc940)      |Network 10.0.2.16 is up!
15:44:55 |moler.runner.thread-pool                 |done & unsubscribing NetworkUpDetector(id:2dfc940, using ThreadedMolerConnection(id:2dfc358)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC400>>])
15:44:55 |moler.runner.thread-pool                 |returning result NetworkUpDetector(id:2dfc940)
15:44:55 |moler.runner.thread-pool                 |shutting down
15:44:55 |moler.runner.thread-pool                 |done & unsubscribing NetworkUpDetector(id:2dfc748, using ThreadedMolerConnection(id:2de4e80)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFC048>>])
15:44:55 |moler.runner.thread-pool                 |returning result NetworkUpDetector(id:2dfc748)
15:44:55 |moler.runner.thread-pool                 |NetworkUpDetector(id:2dfc940) returned 1528983895.6467679
15:44:55 |moler.user.app-code                      |Network 10.0.2.16 is back "up" from 15:44:55
15:44:55 |moler.runner.thread-pool                 |shutting down
15:44:55 |moler.runner.thread-pool                 |NetworkUpDetector(id:2dfc748) returned 1528983895.641768
15:44:55 |moler.user.app-code                      |Network 10.0.2.15 is back "up" from 15:44:55
15:44:55 |threaded.tcp-connection(localhost:5671)  |connection tcp://localhost:5671 is closed
15:44:55 |threaded.tcp-connection(localhost:5672)  |connection tcp://localhost:5672 is closed
15:44:55 |threaded.ping.tcp-server(5671)           |Ping Sim: ... bye
15:44:55 |threaded.ping.tcp-server(5672)           |Ping Sim: ... bye
15:44:57 |threaded.ping.tcp-server(5671 -> 60274)  |Connection closed
15:44:57 |threaded.ping.tcp-server(5672 -> 60275)  |Connection closed
15:44:57 |moler.runner.thread-pool                 |shutting down
15:44:57 |moler.runner.thread-pool                 |shutting down
15:44:57 |moler.runner.thread-pool                 |shutting down
15:44:57 |moler.runner.thread-pool                 |shutting down
'''
