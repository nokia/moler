# -*- coding: utf-8 -*-
"""
network_down_detectors_on_named_conn_v2.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A fully-functional connection-observer using configured concurrency variant.

This is Layer_3 example:
- shows configuration phase and usage phase
  - configure named connections via config file
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

from moler.connection_factory import get_connection

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


# ==============================================================================
if __name__ == '__main__':
    from threaded_ping_server import start_ping_servers, stop_ping_servers
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
        format='%(asctime)s |%(name)-40s |%(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )
    connections2serve = [(('localhost', 5671), '10.0.2.15'),
                         (('localhost', 5672), '10.0.2.16')]
    connections2observe4ip = [(('localhost', 5671), 'net_1', '10.0.2.15'),
                              (('localhost', 5672), 'net_2', '10.0.2.16')]
    servers = start_ping_servers(connections2serve)
    main(connections2observe4ip)
    stop_ping_servers(servers)

'''
LOG OUTPUT

20:44:51 |threaded.ping.tcp-server(5671)           |Ping Sim started at tcp://localhost:5671
20:44:51 |threaded.ping.tcp-server(5671)           |Ping Sim started at tcp://localhost:5671
20:44:51 |moler.runner.thread-pool                 |created
20:44:51 |moler.runner.thread-pool                 |created own executor <concurrent.futures.thread.ThreadPoolExecutor object at 0x0000000002DFE240>
20:44:51 |moler.runner.thread-pool                 |created
20:44:51 |moler.runner.thread-pool                 |created own executor <concurrent.futures.thread.ThreadPoolExecutor object at 0x0000000002DFE4E0>
20:44:51 |moler.user.app-code                      |observe 10.0.2.15 on tcp://localhost:5671 using NetworkDownDetector(id:2dfe080)
20:44:51 |moler.runner.thread-pool                 |go background: NetworkDownDetector(id:2dfe080, using ObservableConnection(id:2de4fd0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DE4DD8>>])
20:44:51 |moler.runner.thread-pool                 |subscribing for data NetworkDownDetector(id:2dfe080, using ObservableConnection(id:2de4fd0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DE4DD8>>])
20:44:51 |moler.runner.thread-pool                 |created
20:44:51 |moler.runner.thread-pool                 |created own executor <concurrent.futures.thread.ThreadPoolExecutor object at 0x0000000002DFEB70>
20:44:51 |moler.runner.thread-pool                 |created
20:44:51 |moler.runner.thread-pool                 |created own executor <concurrent.futures.thread.ThreadPoolExecutor object at 0x0000000002DFECF8>
20:44:51 |moler.user.app-code                      |observe 10.0.2.16 on tcp://localhost:5672 using NetworkDownDetector(id:2dfea58)
20:44:51 |moler.runner.thread-pool                 |go background: NetworkDownDetector(id:2dfea58, using ObservableConnection(id:2dfe940)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFE9E8>>])
20:44:51 |moler.runner.thread-pool                 |subscribing for data NetworkDownDetector(id:2dfea58, using ObservableConnection(id:2dfe940)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFE9E8>>])
20:44:51 |moler.runner.thread-pool                 |go foreground: NetworkDownDetector(id:2dfe080, using ObservableConnection(id:2de4fd0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DE4DD8>>]) - await max. 10 [sec]
20:44:51 |moler.connection.net_1                   |

20:44:51 |moler.runner.thread-pool                 |go foreground: NetworkDownDetector(id:2dfea58, using ObservableConnection(id:2dfe940)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFE9E8>>]) - await max. 10 [sec]
20:44:51 |moler.connection.net_2                   |

20:44:52 |moler.connection.net_1                   |greg@debian:~$ ping 10.0.2.15

20:44:52 |moler.connection.net_2                   |greg@debian:~$ ping 10.0.2.16

20:44:53 |moler.connection.net_1                   |PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.

20:44:53 |moler.connection.net_2                   |PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.

20:44:54 |moler.connection.net_1                   |64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms

20:44:54 |moler.connection.net_2                   |64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms

20:44:55 |moler.connection.net_1                   |64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms

20:44:55 |moler.connection.net_2                   |64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms

20:44:56 |moler.connection.net_1                   |64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms

20:44:56 |moler.connection.net_2                   |64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms

20:44:57 |moler.connection.net_1                   |ping: sendmsg: Network is unreachable

20:44:57 |moler.NetworkDownDetector(id:2dfe080)    |Network 10.0.2.15 is down!
20:44:57 |moler.connection.net_2                   |ping: sendmsg: Network is unreachable

20:44:57 |moler.NetworkDownDetector(id:2dfea58)    |Network 10.0.2.16 is down!
20:44:57 |moler.runner.thread-pool                 |done & unsubscribing NetworkDownDetector(id:2dfe080, using ObservableConnection(id:2de4fd0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DE4DD8>>])
20:44:57 |moler.runner.thread-pool                 |returning result NetworkDownDetector(id:2dfe080)
20:44:57 |moler.runner.thread-pool                 |shutting down
20:44:57 |moler.runner.thread-pool                 |done & unsubscribing NetworkDownDetector(id:2dfea58, using ObservableConnection(id:2dfe940)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFE9E8>>])
20:44:57 |moler.runner.thread-pool                 |returning result NetworkDownDetector(id:2dfea58)
20:44:57 |moler.runner.thread-pool                 |shutting down
20:44:57 |moler.runner.thread-pool                 |NetworkDownDetector(id:2dfe080) returned 1529001897.317741
20:44:57 |moler.user.app-code                      |Network 10.0.2.15 is down from 20:44:57
20:44:57 |moler.user.app-code                      |observe 10.0.2.15 on tcp://localhost:5671 using NetworkUpDetector(id:2dfe3c8)
20:44:57 |moler.runner.thread-pool                 |go background: NetworkUpDetector(id:2dfe3c8, using ObservableConnection(id:2de4fd0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DE4DD8>>])
20:44:57 |moler.runner.thread-pool                 |subscribing for data NetworkUpDetector(id:2dfe3c8, using ObservableConnection(id:2de4fd0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DE4DD8>>])
20:44:57 |moler.runner.thread-pool                 |NetworkDownDetector(id:2dfea58) returned 1529001897.3227408
20:44:57 |moler.user.app-code                      |Network 10.0.2.16 is down from 20:44:57
20:44:57 |moler.user.app-code                      |observe 10.0.2.16 on tcp://localhost:5672 using NetworkUpDetector(id:2dfedd8)
20:44:57 |moler.runner.thread-pool                 |go background: NetworkUpDetector(id:2dfedd8, using ObservableConnection(id:2dfe940)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFE9E8>>])
20:44:57 |moler.runner.thread-pool                 |subscribing for data NetworkUpDetector(id:2dfedd8, using ObservableConnection(id:2dfe940)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFE9E8>>])
20:44:57 |moler.runner.thread-pool                 |go foreground: NetworkUpDetector(id:2dfe3c8, using ObservableConnection(id:2de4fd0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DE4DD8>>]) - await max. None [sec]
20:44:57 |moler.runner.thread-pool                 |go foreground: NetworkUpDetector(id:2dfedd8, using ObservableConnection(id:2dfe940)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFE9E8>>]) - await max. None [sec]
20:44:58 |moler.connection.net_1                   |ping: sendmsg: Network is unreachable

20:44:58 |moler.connection.net_2                   |ping: sendmsg: Network is unreachable

20:44:59 |moler.connection.net_1                   |ping: sendmsg: Network is unreachable

20:44:59 |moler.connection.net_2                   |ping: sendmsg: Network is unreachable

20:45:00 |moler.connection.net_1                   |64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms

20:45:00 |moler.NetworkUpDetector(id:2dfe3c8)      |Network 10.0.2.15 is up!
20:45:00 |moler.connection.net_2                   |64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms

20:45:00 |moler.NetworkUpDetector(id:2dfedd8)      |Network 10.0.2.16 is up!
20:45:00 |moler.runner.thread-pool                 |done & unsubscribing NetworkUpDetector(id:2dfedd8, using ObservableConnection(id:2dfe940)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DFE9E8>>])
20:45:00 |moler.runner.thread-pool                 |returning result NetworkUpDetector(id:2dfedd8)
20:45:00 |moler.runner.thread-pool                 |done & unsubscribing NetworkUpDetector(id:2dfe3c8, using ObservableConnection(id:2de4fd0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DE4DD8>>])
20:45:00 |moler.runner.thread-pool                 |returning result NetworkUpDetector(id:2dfe3c8)
20:45:00 |moler.runner.thread-pool                 |shutting down
20:45:00 |moler.runner.thread-pool                 |NetworkUpDetector(id:2dfedd8) returned 1529001900.3227408
20:45:00 |moler.user.app-code                      |Network 10.0.2.16 is back "up" from 20:45:00
20:45:00 |moler.runner.thread-pool                 |shutting down
20:45:00 |moler.runner.thread-pool                 |NetworkUpDetector(id:2dfe3c8) returned 1529001900.319741
20:45:00 |moler.user.app-code                      |Network 10.0.2.15 is back "up" from 20:45:00
20:45:00 |threaded.ping.tcp-server(5671)           |Ping Sim: ... bye
20:45:00 |threaded.ping.tcp-server(5671)           |Ping Sim: ... bye
20:45:00 |moler.runner.thread-pool                 |shutting down
20:45:00 |moler.runner.thread-pool                 |shutting down
20:45:00 |moler.runner.thread-pool                 |shutting down
20:45:00 |moler.runner.thread-pool                 |shutting down
'''
