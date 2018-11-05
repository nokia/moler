# -*- coding: utf-8 -*-
"""
asyncio_runner_with_async_functions.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Shows how to use connection observers inside 'async def xxx()' functions.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import logging
import sys
import os
import time
import asyncio

from moler.connection import get_connection
from moler.asyncio_runner import AsyncioRunner

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))  # allow finding modules in examples/

from network_toggle_observers import NetworkDownDetector, NetworkUpDetector


# ===================== Moler's connection-observer usage ======================


async def ping_observing_task(ext_io_connection, ping_ip):
    """
    Here external-IO connection is abstract - we don't know its type.
    What we know is just that it has .moler_connection attribute.
    """

    logger = logging.getLogger('moler.user.app-code')
    conn_addr = str(ext_io_connection)

    # Layer 2 of Moler's usage (ext_io_connection + runner):
    # 3. create observers on Moler's connection
    net_down_detector = NetworkDownDetector(ping_ip,
                                            connection=ext_io_connection.moler_connection,
                                            runner=AsyncioRunner())
    net_up_detector = NetworkUpDetector(ping_ip,
                                        connection=ext_io_connection.moler_connection,
                                        runner=AsyncioRunner())

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
async def main(connections2observe4ip):
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
        # client_task= asyncio.ensure_future(ping_observing_task(tcp_connection, ping_ip))
        connections.append(ping_observing_task(tcp_connection, ping_ip))
    # await observers job to be done
    completed, pending = await asyncio.wait(connections)


# ==============================================================================
if __name__ == '__main__':
    from threaded_ping_server import start_ping_servers, stop_ping_servers
    from asyncio_common import run_via_asyncio, configure_logging
    import os
    from moler.config import load_config
    # -------------------------------------------------------------------
    # Configure moler connections (backend code)
    # 1) configure variant by YAML config file
    # 2) ver.2 - configure named connections by YAML config file
    load_config(config=os.path.join(os.path.dirname(__file__), "..", "named_connections.yml"))

    # 3) take default class used to realize tcp-threaded-connection
    # -------------------------------------------------------------------

    configure_logging()

    connections2serve = [(('localhost', 5671), '10.0.2.15'),
                         (('localhost', 5672), '10.0.2.16')]
    connections2observe4ip = [(('localhost', 5671), 'net_1', '10.0.2.15'),
                              (('localhost', 5672), 'net_2', '10.0.2.16')]
    servers = start_ping_servers(connections2serve)

    try:
        run_via_asyncio(main(connections2observe4ip))

    finally:
        stop_ping_servers(servers)

'''
LOG OUTPUT

 |threaded.ping.tcp-server(5671)                |   MainThread |Ping Sim started at tcp://localhost:5671
 |threaded.ping.tcp-server(5672)                |   MainThread |Ping Sim started at tcp://localhost:5672
 |asyncio                                       |   MainThread |Using selector: EpollSelector
 |asyncio.main                                  |   MainThread |starting events loop ...
 |moler.runner.asyncio                          |   MainThread |created
 |moler.runner.asyncio                          |   MainThread |created
 |moler.user.app-code                           |   MainThread |observe 10.0.2.15 on tcp://localhost:5671 using NetworkDownDetector(id:7f58967041d0)
 |moler.runner.asyncio                          |   MainThread |go background: NetworkDownDetector(id:7f58967041d0, using ObservableConnection(id:7f58966f2eb8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704390>>])
 |moler.runner.asyncio                          |   MainThread |start feeding(NetworkDownDetector(id:7f58967041d0))
 |moler.runner.asyncio                          |   MainThread |feed subscribing for data NetworkDownDetector(id:7f58967041d0, using ObservableConnection(id:7f58966f2eb8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704390>>])
 |moler.runner.asyncio                          |   MainThread |feeding(NetworkDownDetector(id:7f58967041d0)) started
 |moler.runner.asyncio                          |   MainThread |go foreground: NetworkDownDetector(id:7f58967041d0, using ObservableConnection(id:7f58966f2eb8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704390>>]) - await max. 10 [sec]
 |moler.runner.asyncio                          |   MainThread |created
 |moler.runner.asyncio                          |   MainThread |created
 |moler.user.app-code                           |   MainThread |observe 10.0.2.16 on tcp://localhost:5672 using NetworkDownDetector(id:7f5896704710)
 |moler.runner.asyncio                          |   MainThread |go background: NetworkDownDetector(id:7f5896704710, using ObservableConnection(id:7f5896704080)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704278>>])
 |moler.runner.asyncio                          |   MainThread |start feeding(NetworkDownDetector(id:7f5896704710))
 |moler.runner.asyncio                          |   MainThread |feed subscribing for data NetworkDownDetector(id:7f5896704710, using ObservableConnection(id:7f5896704080)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704278>>])
 |moler.runner.asyncio                          |   MainThread |feeding(NetworkDownDetector(id:7f5896704710)) started
 |moler.runner.asyncio                          |   MainThread |go foreground: NetworkDownDetector(id:7f5896704710, using ObservableConnection(id:7f5896704080)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704278>>]) - await max. 10 [sec]
 |moler.runner.asyncio                          |   MainThread |START OF feed(NetworkDownDetector(id:7f58967041d0))
 |moler.runner.asyncio                          |   MainThread |START OF feed(NetworkDownDetector(id:7f5896704710))
 |threaded.ping.tcp-server(5672 -> 43235)       |     Thread-5 |connection accepted - client at tcp://127.0.0.1:43235
 |threaded.ping.tcp-server(5671 -> 49431)       |     Thread-6 |connection accepted - client at tcp://127.0.0.1:49431
 |moler.net_2                                   |     Thread-4 |

 |moler.net_1                                   |     Thread-3 |

 |moler.net_2                                   |     Thread-4 |greg@debian:~$ ping 10.0.2.16

 |moler.net_1                                   |     Thread-3 |greg@debian:~$ ping 10.0.2.15

 |moler.net_2                                   |     Thread-4 |PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.

 |moler.net_1                                   |     Thread-3 |PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.

 |moler.net_2                                   |     Thread-4 |64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms

 |moler.net_1                                   |     Thread-3 |64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms

 |moler.net_2                                   |     Thread-4 |64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms

 |moler.net_1                                   |     Thread-3 |64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms

 |moler.net_2                                   |     Thread-4 |64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms

 |moler.net_1                                   |     Thread-3 |64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms

 |moler.net_1                                   |     Thread-3 |ping: sendmsg: Network is unreachable

 |moler.NetworkDownDetector(id:7f58967041d0)    |     Thread-3 |Network 10.0.2.15 is down!
 |moler.net_2                                   |     Thread-4 |ping: sendmsg: Network is unreachable

 |moler.NetworkDownDetector(id:7f5896704710)    |     Thread-4 |Network 10.0.2.16 is down!
 |moler.runner.asyncio                          |   MainThread |NetworkDownDetector(id:7f5896704710) returned 1541419564.8677728
 |moler.user.app-code                           |   MainThread |Network 10.0.2.16 is down from 13:06:04
 |moler.user.app-code                           |   MainThread |observe 10.0.2.16 on tcp://localhost:5672 using NetworkUpDetector(id:7f58967046d8)
 |moler.runner.asyncio                          |   MainThread |go background: NetworkUpDetector(id:7f58967046d8, using ObservableConnection(id:7f5896704080)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704278>>])
 |moler.runner.asyncio                          |   MainThread |start feeding(NetworkUpDetector(id:7f58967046d8))
 |moler.runner.asyncio                          |   MainThread |feed subscribing for data NetworkUpDetector(id:7f58967046d8, using ObservableConnection(id:7f5896704080)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704278>>])
 |moler.runner.asyncio                          |   MainThread |feeding(NetworkUpDetector(id:7f58967046d8)) started
 |moler.runner.asyncio                          |   MainThread |go foreground: NetworkUpDetector(id:7f58967046d8, using ObservableConnection(id:7f5896704080)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704278>>]) - await max. None [sec]
 |moler.runner.asyncio                          |   MainThread |feed done & unsubscribing NetworkDownDetector(id:7f58967041d0, using ObservableConnection(id:7f58966f2eb8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704390>>])
 |moler.runner.asyncio                          |   MainThread |feed returning result NetworkDownDetector(id:7f58967041d0)
 |moler.runner.asyncio                          |   MainThread |END   OF feed(NetworkDownDetector(id:7f58967041d0))
 |moler.runner.asyncio                          |   MainThread |feed done & unsubscribing NetworkDownDetector(id:7f5896704710, using ObservableConnection(id:7f5896704080)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704278>>])
 |moler.runner.asyncio                          |   MainThread |feed returning result NetworkDownDetector(id:7f5896704710)
 |moler.runner.asyncio                          |   MainThread |END   OF feed(NetworkDownDetector(id:7f5896704710))
 |moler.runner.asyncio                          |   MainThread |START OF feed(NetworkUpDetector(id:7f58967046d8))
 |moler.net_1                                   |     Thread-3 |ping: sendmsg: Network is unreachable

 |moler.net_2                                   |     Thread-4 |ping: sendmsg: Network is unreachable

 |moler.net_1                                   |     Thread-3 |ping: sendmsg: Network is unreachable

 |moler.net_2                                   |     Thread-4 |ping: sendmsg: Network is unreachable

 |moler.net_1                                   |     Thread-3 |64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms

 |moler.net_2                                   |     Thread-4 |64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms

 |moler.NetworkUpDetector(id:7f58967046d8)      |     Thread-4 |Network 10.0.2.16 is up!
 |moler.runner.asyncio                          |   MainThread |NetworkUpDetector(id:7f58967046d8) returned 1541419567.8749208
 |moler.user.app-code                           |   MainThread |Network 10.0.2.16 is back "up" from 13:06:07
 |asyncio                                       |   MainThread |Exception in callback <TaskStepMethWrapper object at 0x7f5896704208>()
handle: <Handle <TaskStepMethWrapper object at 0x7f5896704208>()>
Traceback (most recent call last):
  File "/opt/ute/python3/lib/python3.6/asyncio/events.py", line 127, in _run
    self._callback(*self._args)
KeyError: <_UnixSelectorEventLoop running=True closed=False debug=False>
 |moler.runner.asyncio                          |   MainThread |feed done & unsubscribing NetworkUpDetector(id:7f58967046d8, using ObservableConnection(id:7f5896704080)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704278>>])
 |moler.runner.asyncio                          |   MainThread |feed returning result NetworkUpDetector(id:7f58967046d8)
 |moler.runner.asyncio                          |   MainThread |END   OF feed(NetworkUpDetector(id:7f58967046d8))
 |moler.runner.asyncio                          |   MainThread |NetworkDownDetector(id:7f58967041d0) returned 1541419564.8671029
 |moler.user.app-code                           |   MainThread |Network 10.0.2.15 is down from 13:06:04
 |moler.user.app-code                           |   MainThread |observe 10.0.2.15 on tcp://localhost:5671 using NetworkUpDetector(id:7f58967044e0)
 |moler.runner.asyncio                          |   MainThread |go background: NetworkUpDetector(id:7f58967044e0, using ObservableConnection(id:7f58966f2eb8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704390>>])
 |moler.runner.asyncio                          |   MainThread |start feeding(NetworkUpDetector(id:7f58967044e0))
 |moler.runner.asyncio                          |   MainThread |feed subscribing for data NetworkUpDetector(id:7f58967044e0, using ObservableConnection(id:7f58966f2eb8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704390>>])
 |moler.runner.asyncio                          |   MainThread |feeding(NetworkUpDetector(id:7f58967044e0)) started
 |moler.runner.asyncio                          |   MainThread |go foreground: NetworkUpDetector(id:7f58967044e0, using ObservableConnection(id:7f58966f2eb8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704390>>]) - await max. None [sec]
 |moler.runner.asyncio                          |   MainThread |START OF feed(NetworkUpDetector(id:7f58967044e0))
 |moler.net_1                                   |     Thread-3 |64 bytes from 10.0.2.15: icmp_req=8 ttl=64 time=0.056 ms

 |moler.NetworkUpDetector(id:7f58967044e0)      |     Thread-3 |Network 10.0.2.15 is up!
 |moler.runner.asyncio                          |   MainThread |NetworkUpDetector(id:7f58967044e0) returned 1541419568.8756313
 |moler.user.app-code                           |   MainThread |Network 10.0.2.15 is back "up" from 13:06:08
 |asyncio                                       |   MainThread |Exception in callback <TaskStepMethWrapper object at 0x7f5896f5cef0>()
handle: <Handle <TaskStepMethWrapper object at 0x7f5896f5cef0>()>
Traceback (most recent call last):
  File "/opt/ute/python3/lib/python3.6/asyncio/events.py", line 127, in _run
    self._callback(*self._args)
KeyError: <_UnixSelectorEventLoop running=True closed=False debug=False>
 |moler.runner.asyncio                          |   MainThread |feed done & unsubscribing NetworkUpDetector(id:7f58967044e0, using ObservableConnection(id:7f58966f2eb8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f5896704390>>])
 |moler.runner.asyncio                          |   MainThread |feed returning result NetworkUpDetector(id:7f58967044e0)
 |moler.runner.asyncio                          |   MainThread |END   OF feed(NetworkUpDetector(id:7f58967044e0))
 |asyncio.main                                  |   MainThread |cancelling all remaining tasks
 |asyncio.main                                  |   MainThread |closing events loop ...
 |asyncio.main                                  |   MainThread |... events loop closed
 |threaded.ping.tcp-server(5671)                |     Thread-1 |Ping Sim: ... bye
 |threaded.ping.tcp-server(5672)                |     Thread-2 |Ping Sim: ... bye
 |threaded.ping.tcp-server(5672 -> 43235)       |     Thread-5 |Connection closed
 |threaded.ping.tcp-server(5671 -> 49431)       |     Thread-6 |Connection closed
 |moler.runner.asyncio                          |      Dummy-7 |shutting down
 |moler.runner.asyncio                          |      Dummy-7 |shutting down
 |moler.runner.asyncio                          |      Dummy-7 |shutting down
 |moler.runner.asyncio                          |      Dummy-7 |shutting down
'''
