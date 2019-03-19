# -*- coding: utf-8 -*-
"""
network_down_detectors_on_tcp_conn_v1.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A fully-functional connection-observer using configured concurrency variant.

This is Layer_3 example:
- shows configuration phase and usage phase
  - configuration via python code
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

from moler.connection import get_connection

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
        tcp_connection.moler_connection.name = "{}:{}".format(host, port)
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
    # don't configure class used to realize tcp-threaded-connection - take default one
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

19:54:20 |threaded.ping.tcp-server(5671)           |Ping Sim started at tcp://localhost:5671
19:54:20 |threaded.ping.tcp-server(5672)           |Ping Sim started at tcp://localhost:5672
19:54:20 |moler.runner.thread-pool                 |created
19:54:20 |moler.runner.thread-pool                 |created own executor <concurrent.futures.thread.ThreadPoolExecutor object at 0x0000000002E0D160>
19:54:20 |moler.runner.thread-pool                 |created
19:54:20 |moler.runner.thread-pool                 |created
19:54:20 |moler.runner.thread-pool                 |created own executor <concurrent.futures.thread.ThreadPoolExecutor object at 0x0000000002E0D550>
19:54:20 |moler.runner.thread-pool                 |created own executor <concurrent.futures.thread.ThreadPoolExecutor object at 0x0000000002E0D668>
19:54:20 |moler.runner.thread-pool                 |created
19:54:20 |moler.user.app-code                      |observe 10.0.2.15 on tcp://localhost:5671 using NetworkDownDetector(id:2e0d080)
19:54:20 |moler.runner.thread-pool                 |created own executor <concurrent.futures.thread.ThreadPoolExecutor object at 0x0000000002E0D978>
19:54:20 |moler.runner.thread-pool                 |go background: NetworkDownDetector(id:2e0d080, using ObservableConnection(id:2df3da0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DF3EF0>>])
19:54:20 |moler.user.app-code                      |observe 10.0.2.16 on tcp://localhost:5672 using NetworkDownDetector(id:2e0d518)
19:54:20 |moler.runner.thread-pool                 |subscribing for data NetworkDownDetector(id:2e0d080, using ObservableConnection(id:2df3da0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DF3EF0>>])
19:54:20 |moler.runner.thread-pool                 |go background: NetworkDownDetector(id:2e0d518, using ObservableConnection(id:2e0d240)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002E0D2B0>>])
19:54:20 |moler.runner.thread-pool                 |subscribing for data NetworkDownDetector(id:2e0d518, using ObservableConnection(id:2e0d240)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002E0D2B0>>])
19:54:20 |threaded.ping.tcp-server(5672 -> 59439)  |connection accepted - client at tcp://127.0.0.1:59439
19:54:20 |moler.runner.thread-pool                 |go foreground: NetworkDownDetector(id:2e0d518, using ObservableConnection(id:2e0d240)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002E0D2B0>>]) - await max. 10 [sec]
19:54:20 |moler.connection.localhost:5672          |

19:54:20 |threaded.ping.tcp-server(5671 -> 59440)  |connection accepted - client at tcp://127.0.0.1:59440
19:54:20 |moler.runner.thread-pool                 |go foreground: NetworkDownDetector(id:2e0d080, using ObservableConnection(id:2df3da0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DF3EF0>>]) - await max. 10 [sec]
19:54:20 |moler.connection.localhost:5671          |

19:54:21 |moler.connection.localhost:5672          |greg@debian:~$ ping 10.0.2.16

19:54:21 |moler.connection.localhost:5671          |greg@debian:~$ ping 10.0.2.15

19:54:22 |moler.connection.localhost:5672          |PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.

19:54:22 |moler.connection.localhost:5671          |PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.

19:54:23 |moler.connection.localhost:5672          |64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms

19:54:23 |moler.connection.localhost:5671          |64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms

19:54:24 |moler.connection.localhost:5672          |64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms

19:54:24 |moler.connection.localhost:5671          |64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms

19:54:25 |moler.connection.localhost:5672          |64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms

19:54:25 |moler.connection.localhost:5671          |64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms

19:54:26 |moler.connection.localhost:5672          |ping: sendmsg: Network is unreachable

19:54:26 |moler.NetworkDownDetector(id:2e0d518)    |Network 10.0.2.16 is down!
19:54:26 |moler.connection.localhost:5671          |ping: sendmsg: Network is unreachable

19:54:26 |moler.NetworkDownDetector(id:2e0d080)    |Network 10.0.2.15 is down!
19:54:26 |moler.runner.thread-pool                 |done & unsubscribing NetworkDownDetector(id:2e0d518, using ObservableConnection(id:2e0d240)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002E0D2B0>>])
19:54:26 |moler.runner.thread-pool                 |done & unsubscribing NetworkDownDetector(id:2e0d080, using ObservableConnection(id:2df3da0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DF3EF0>>])
19:54:26 |moler.runner.thread-pool                 |returning result NetworkDownDetector(id:2e0d518)
19:54:26 |moler.runner.thread-pool                 |returning result NetworkDownDetector(id:2e0d080)
19:54:26 |moler.runner.thread-pool                 |shutting down
19:54:26 |moler.runner.thread-pool                 |shutting down
19:54:26 |moler.runner.thread-pool                 |NetworkDownDetector(id:2e0d518) returned 1528998866.6692297
19:54:26 |moler.runner.thread-pool                 |NetworkDownDetector(id:2e0d080) returned 1528998866.6722302
19:54:26 |moler.user.app-code                      |Network 10.0.2.16 is down from 19:54:26
19:54:26 |moler.user.app-code                      |Network 10.0.2.15 is down from 19:54:26
19:54:26 |moler.user.app-code                      |observe 10.0.2.16 on tcp://localhost:5672 using NetworkUpDetector(id:2e0d7f0)
19:54:26 |moler.user.app-code                      |observe 10.0.2.15 on tcp://localhost:5671 using NetworkUpDetector(id:2e0d5f8)
19:54:26 |moler.runner.thread-pool                 |go background: NetworkUpDetector(id:2e0d7f0, using ObservableConnection(id:2e0d240)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002E0D2B0>>])
19:54:26 |moler.runner.thread-pool                 |go background: NetworkUpDetector(id:2e0d5f8, using ObservableConnection(id:2df3da0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DF3EF0>>])
19:54:26 |moler.runner.thread-pool                 |subscribing for data NetworkUpDetector(id:2e0d7f0, using ObservableConnection(id:2e0d240)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002E0D2B0>>])
19:54:26 |moler.runner.thread-pool                 |subscribing for data NetworkUpDetector(id:2e0d5f8, using ObservableConnection(id:2df3da0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DF3EF0>>])
19:54:26 |moler.runner.thread-pool                 |go foreground: NetworkUpDetector(id:2e0d7f0, using ObservableConnection(id:2e0d240)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002E0D2B0>>]) - await max. None [sec]
19:54:26 |moler.runner.thread-pool                 |go foreground: NetworkUpDetector(id:2e0d5f8, using ObservableConnection(id:2df3da0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DF3EF0>>]) - await max. None [sec]
19:54:27 |moler.connection.localhost:5672          |ping: sendmsg: Network is unreachable

19:54:27 |moler.connection.localhost:5671          |ping: sendmsg: Network is unreachable

19:54:28 |moler.connection.localhost:5672          |ping: sendmsg: Network is unreachable

19:54:28 |moler.connection.localhost:5671          |ping: sendmsg: Network is unreachable

19:54:29 |moler.connection.localhost:5672          |64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms

19:54:29 |moler.NetworkUpDetector(id:2e0d7f0)      |Network 10.0.2.16 is up!
19:54:29 |moler.connection.localhost:5671          |64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms

19:54:29 |moler.NetworkUpDetector(id:2e0d5f8)      |Network 10.0.2.15 is up!
19:54:29 |moler.runner.thread-pool                 |done & unsubscribing NetworkUpDetector(id:2e0d5f8, using ObservableConnection(id:2df3da0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002DF3EF0>>])
19:54:29 |moler.runner.thread-pool                 |returning result NetworkUpDetector(id:2e0d5f8)
19:54:29 |moler.runner.thread-pool                 |done & unsubscribing NetworkUpDetector(id:2e0d7f0, using ObservableConnection(id:2e0d240)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000002E0D2B0>>])
19:54:29 |moler.runner.thread-pool                 |shutting down
19:54:29 |moler.runner.thread-pool                 |returning result NetworkUpDetector(id:2e0d7f0)
19:54:29 |moler.runner.thread-pool                 |NetworkUpDetector(id:2e0d5f8) returned 1528998869.6745303
19:54:29 |moler.user.app-code                      |Network 10.0.2.15 is back "up" from 19:54:29
19:54:29 |moler.runner.thread-pool                 |shutting down
19:54:29 |moler.runner.thread-pool                 |NetworkUpDetector(id:2e0d7f0) returned 1528998869.67153
19:54:29 |moler.user.app-code                      |Network 10.0.2.16 is back "up" from 19:54:29
19:54:29 |threaded.ping.tcp-server(5671)           |Ping Sim: ... bye
19:54:29 |threaded.ping.tcp-server(5672)           |Ping Sim: ... bye
19:54:31 |threaded.ping.tcp-server(5672 -> 59439)  |Connection closed
19:54:31 |threaded.ping.tcp-server(5671 -> 59440)  |Connection closed
19:54:31 |moler.runner.thread-pool                 |shutting down
19:54:31 |moler.runner.thread-pool                 |shutting down
19:54:31 |moler.runner.thread-pool                 |shutting down
19:54:31 |moler.runner.thread-pool                 |shutting down
'''
