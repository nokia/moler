# -*- coding: utf-8 -*-
"""
asyncio_in_thread_runner.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Shows how to use connection observers inside code that uses only
'async def xxx()' functions (no threads/processes).
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
from moler.asyncio_runner import AsyncioInThreadRunner
from moler.exceptions import ConnectionObserverTimeout

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
                                            runner=AsyncioInThreadRunner())
    net_up_detector = NetworkUpDetector(ping_ip,
                                        connection=ext_io_connection.moler_connection,
                                        runner=AsyncioInThreadRunner())

    info = '{} on {} using {}'.format(ping_ip, conn_addr, net_down_detector)
    logger.debug('observe ' + info)

    # 4. start observer (nonblocking, using as future)
    net_down_detector.start()  # should be started before we open connection
    # to not loose first data on connection

    with ext_io_connection:
        # 5. await that observer to complete
        try:
            # net_down_time = await net_down_detector
            net_down_time = net_down_detector.await_done(timeout=10)
        #     net_down_time = await asyncio.wait_for(net_down_detector, timeout=2)  # =10 --> no TimeoutError
            timestamp = time.strftime("%H:%M:%S", time.localtime(net_down_time))
            logger.debug('Network {} is down from {}'.format(ping_ip, timestamp))
        except asyncio.TimeoutError:
            logger.debug('Network down detector timed out (asyncio timeout)')
        except ConnectionObserverTimeout:
            logger.debug('Network down detector timed out (moler timeout)')
        #
        # await asyncio.sleep(5)

        # 6. call next observer (blocking till completes)
        info = '{} on {} using {}'.format(ping_ip, conn_addr, net_up_detector)
        logger.debug('observe ' + info)
        # using as synchronous function (so we want verb to express action)
        detect_network_up = net_up_detector
        net_up_time = await detect_network_up
        timestamp = time.strftime("%H:%M:%S", time.localtime(net_up_time))
        logger.debug('Network {} is back "up" from {}'.format(ping_ip, timestamp))
    logger.debug('exiting ping_observing_task')


# ==============================================================================
async def main(connections2observe4ip):
    logger = logging.getLogger('asyncio.main')
    event_loop = asyncio.get_event_loop()

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
        con_logger = logging.getLogger('tcp-thrd-io.{}'.format(connection_name))
        tcp_connection = get_connection(name=connection_name, logger=con_logger)
        tcp_connection.moler_connection.name = connection_name
        # client_task= asyncio.ensure_future(ping_observing_task(tcp_connection, ping_ip))
        connections.append(ping_observing_task(tcp_connection, ping_ip))
    # await observers job to be done
    completed, pending = await asyncio.wait(connections)
    logger.debug('after all ping_observing_task')


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
 |moler.runner.asyncio-in-thrd:0                |   MainThread |created
 |moler.runner.asyncio-in-thrd:0                |   MainThread |created
 |moler.user.app-code                           |   MainThread |observe 10.0.2.16 on tcp://localhost:5672 using NetworkDownDetector(id:7f54e6875550)
 |moler.runner.asyncio-in-thrd:7f54e6875550     |   MainThread |go background: NetworkDownDetector(id:7f54e6875550, using ObservableConnection(id:7f54e68752e8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875390>>])
 |asyncio                                       |   MainThread |Using selector: EpollSelector
 |moler.runner.asyncio-in-thrd:7f54e6875550     |     Thread-3 |starting new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:7f54e6875550     |   MainThread |started new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:7f54e6875550     |     Thread-3 |will await stop_event ...
 |moler.runner.asyncio-in-thrd:7f54e6875550     |     Thread-3 |START OF feed(NetworkDownDetector(id:7f54e6875550))
 |moler.runner.asyncio-in-thrd:7f54e6875550     |     Thread-3 |start feeding(NetworkDownDetector(id:7f54e6875550))
 |moler.runner.asyncio-in-thrd:7f54e6875550     |     Thread-3 |feed subscribing for data NetworkDownDetector(id:7f54e6875550, using ObservableConnection(id:7f54e68752e8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875390>>])
 |moler.runner.asyncio-in-thrd:7f54e6875550     |     Thread-3 |feeding(NetworkDownDetector(id:7f54e6875550)) started
 |tcp-thrd-io.net_2                             |   MainThread |connecting to tcp://localhost:5672
 |tcp-thrd-io.net_2                             |   MainThread |connection tcp://localhost:5672 is open
 |threaded.ping.tcp-server(5672 -> 43232)       |     Thread-5 |connection accepted - client at tcp://127.0.0.1:43232
 |moler.runner.asyncio-in-thrd:7f54e6875550     |   MainThread |go foreground: NetworkDownDetector(id:7f54e6875550, using ObservableConnection(id:7f54e68752e8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875390>>]) - await max. 10 [sec]
 |tcp-thrd-io.net_2                             |     Thread-4 |< b'\n'
 |moler.net_2                                   |     Thread-4 |

 |tcp-thrd-io.net_2                             |     Thread-4 |< b'greg@debian:~$ ping 10.0.2.16\n'
 |moler.net_2                                   |     Thread-4 |greg@debian:~$ ping 10.0.2.16

 |tcp-thrd-io.net_2                             |     Thread-4 |< b'PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.\n'
 |moler.net_2                                   |     Thread-4 |PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.

 |tcp-thrd-io.net_2                             |     Thread-4 |< b'64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms\n'
 |moler.net_2                                   |     Thread-4 |64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms

 |tcp-thrd-io.net_2                             |     Thread-4 |< b'64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms\n'
 |moler.net_2                                   |     Thread-4 |64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms

 |tcp-thrd-io.net_2                             |     Thread-4 |< b'64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms\n'
 |moler.net_2                                   |     Thread-4 |64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms

 |tcp-thrd-io.net_2                             |     Thread-4 |< b'ping: sendmsg: Network is unreachable\n'
 |moler.net_2                                   |     Thread-4 |ping: sendmsg: Network is unreachable

 |moler.NetworkDownDetector(id:7f54e6875550)    |     Thread-4 |Network 10.0.2.16 is down!
 |moler.runner.asyncio-in-thrd:7f54e6875550     |     Thread-3 |feed done & unsubscribing NetworkDownDetector(id:7f54e6875550, using ObservableConnection(id:7f54e68752e8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875390>>])
 |moler.runner.asyncio-in-thrd:7f54e6875550     |     Thread-3 |feed returning result NetworkDownDetector(id:7f54e6875550)
 |moler.runner.asyncio-in-thrd:7f54e6875550     |     Thread-3 |END   OF feed(NetworkDownDetector(id:7f54e6875550))
 |moler.runner.asyncio-in-thrd:7f54e6875550     |   MainThread |shutting down
 |moler.runner.asyncio-in-thrd:7f54e6875550     |   MainThread |NetworkDownDetector(id:7f54e6875550) returned 1541419487.46808
 |moler.user.app-code                           |   MainThread |Network 10.0.2.16 is down from 13:04:47
 |moler.user.app-code                           |   MainThread |observe 10.0.2.16 on tcp://localhost:5672 using NetworkUpDetector(id:7f54e6875668)
 |moler.runner.asyncio-in-thrd:7f54e6875668     |   MainThread |go background: NetworkUpDetector(id:7f54e6875668, using ObservableConnection(id:7f54e68752e8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875390>>])
 |asyncio                                       |   MainThread |Using selector: EpollSelector
 |asyncio                                       |     Thread-3 |poll took 1.067 ms: 1 events
 |moler.runner.asyncio-in-thrd:7f54e6875550     |     Thread-3 |... await stop_event done
 |moler.runner.asyncio-in-thrd:7f54e6875550     |     Thread-3 |... asyncio-in-thrd loop done
 |moler.runner.asyncio-in-thrd:7f54e6875668     |     Thread-6 |starting new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:7f54e6875668     |   MainThread |started new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:7f54e6875668     |     Thread-6 |will await stop_event ...
 |moler.runner.asyncio-in-thrd:7f54e6875668     |     Thread-6 |START OF feed(NetworkUpDetector(id:7f54e6875668))
 |moler.runner.asyncio-in-thrd:7f54e6875668     |     Thread-6 |start feeding(NetworkUpDetector(id:7f54e6875668))
 |moler.runner.asyncio-in-thrd:7f54e6875668     |     Thread-6 |feed subscribing for data NetworkUpDetector(id:7f54e6875668, using ObservableConnection(id:7f54e68752e8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875390>>])
 |moler.runner.asyncio-in-thrd:7f54e6875668     |     Thread-6 |feeding(NetworkUpDetector(id:7f54e6875668)) started
 |moler.runner.asyncio-in-thrd:7f54e6875668     |   MainThread |returning iterator for NetworkUpDetector(id:7f54e6875668)
 |moler.runner.asyncio-in-thrd:0                |   MainThread |created
 |moler.runner.asyncio-in-thrd:0                |   MainThread |created
 |moler.user.app-code                           |   MainThread |observe 10.0.2.15 on tcp://localhost:5671 using NetworkDownDetector(id:7f54e16906a0)
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |   MainThread |go background: NetworkDownDetector(id:7f54e16906a0, using ObservableConnection(id:7f54e6875ef0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875160>>])
 |asyncio                                       |   MainThread |Using selector: EpollSelector
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |     Thread-7 |starting new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |     Thread-7 |will await stop_event ...
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |   MainThread |started new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |     Thread-7 |START OF feed(NetworkDownDetector(id:7f54e16906a0))
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |     Thread-7 |start feeding(NetworkDownDetector(id:7f54e16906a0))
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |     Thread-7 |feed subscribing for data NetworkDownDetector(id:7f54e16906a0, using ObservableConnection(id:7f54e6875ef0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875160>>])
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |     Thread-7 |feeding(NetworkDownDetector(id:7f54e16906a0)) started
 |tcp-thrd-io.net_1                             |   MainThread |connecting to tcp://localhost:5671
 |tcp-thrd-io.net_1                             |   MainThread |connection tcp://localhost:5671 is open
 |threaded.ping.tcp-server(5671 -> 49430)       |     Thread-8 |connection accepted - client at tcp://127.0.0.1:49430
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |   MainThread |go foreground: NetworkDownDetector(id:7f54e16906a0, using ObservableConnection(id:7f54e6875ef0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875160>>]) - await max. 10 [sec]
 |tcp-thrd-io.net_1                             |     Thread-9 |< b'\n'
 |moler.net_1                                   |     Thread-9 |

 |tcp-thrd-io.net_2                             |     Thread-4 |< b'ping: sendmsg: Network is unreachable\n'
 |moler.net_2                                   |     Thread-4 |ping: sendmsg: Network is unreachable

 |tcp-thrd-io.net_1                             |     Thread-9 |< b'greg@debian:~$ ping 10.0.2.15\n'
 |moler.net_1                                   |     Thread-9 |greg@debian:~$ ping 10.0.2.15

 |tcp-thrd-io.net_2                             |     Thread-4 |< b'ping: sendmsg: Network is unreachable\n'
 |moler.net_2                                   |     Thread-4 |ping: sendmsg: Network is unreachable

 |tcp-thrd-io.net_1                             |     Thread-9 |< b'PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.\n'
 |moler.net_1                                   |     Thread-9 |PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.

 |tcp-thrd-io.net_2                             |     Thread-4 |< b'64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms\n'
 |moler.net_2                                   |     Thread-4 |64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms

 |moler.NetworkUpDetector(id:7f54e6875668)      |     Thread-4 |Network 10.0.2.16 is up!
 |moler.runner.asyncio-in-thrd:7f54e6875668     |     Thread-6 |feed done & unsubscribing NetworkUpDetector(id:7f54e6875668, using ObservableConnection(id:7f54e68752e8)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875390>>])
 |moler.runner.asyncio-in-thrd:7f54e6875668     |     Thread-6 |feed returning result NetworkUpDetector(id:7f54e6875668)
 |moler.runner.asyncio-in-thrd:7f54e6875668     |     Thread-6 |END   OF feed(NetworkUpDetector(id:7f54e6875668))
 |tcp-thrd-io.net_1                             |     Thread-9 |< b'64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms\n'
 |moler.net_1                                   |     Thread-9 |64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms

 |tcp-thrd-io.net_2                             |     Thread-4 |< b'64 bytes from 10.0.2.16: icmp_req=8 ttl=64 time=0.056 ms\n'
 |moler.net_2                                   |     Thread-4 |64 bytes from 10.0.2.16: icmp_req=8 ttl=64 time=0.056 ms

 |tcp-thrd-io.net_1                             |     Thread-9 |< b'64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms\n'
 |moler.net_1                                   |     Thread-9 |64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms

 |threaded.ping.tcp-server(5672 -> 43232)       |     Thread-5 |Connection closed
 |tcp-thrd-io.net_2                             |     Thread-4 |< b''
 |tcp-thrd-io.net_1                             |     Thread-9 |< b'64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms\n'
 |moler.net_1                                   |     Thread-9 |64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms

 |tcp-thrd-io.net_1                             |     Thread-9 |< b'ping: sendmsg: Network is unreachable\n'
 |moler.net_1                                   |     Thread-9 |ping: sendmsg: Network is unreachable

 |moler.NetworkDownDetector(id:7f54e16906a0)    |     Thread-9 |Network 10.0.2.15 is down!
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |     Thread-7 |feed done & unsubscribing NetworkDownDetector(id:7f54e16906a0, using ObservableConnection(id:7f54e6875ef0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875160>>])
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |     Thread-7 |feed returning result NetworkDownDetector(id:7f54e16906a0)
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |     Thread-7 |END   OF feed(NetworkDownDetector(id:7f54e16906a0))
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |   MainThread |shutting down
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |   MainThread |NetworkDownDetector(id:7f54e16906a0) returned 1541419493.4887183
 |moler.user.app-code                           |   MainThread |Network 10.0.2.15 is down from 13:04:53
 |moler.user.app-code                           |   MainThread |observe 10.0.2.15 on tcp://localhost:5671 using NetworkUpDetector(id:7f54e1690748)
 |moler.runner.asyncio-in-thrd:7f54e1690748     |   MainThread |go background: NetworkUpDetector(id:7f54e1690748, using ObservableConnection(id:7f54e6875ef0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875160>>])
 |asyncio                                       |   MainThread |Using selector: EpollSelector
 |asyncio                                       |     Thread-7 |poll took 0.925 ms: 1 events
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |     Thread-7 |... await stop_event done
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |     Thread-7 |... asyncio-in-thrd loop done
 |moler.runner.asyncio-in-thrd:7f54e1690748     |    Thread-10 |starting new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:7f54e1690748     |   MainThread |started new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:7f54e1690748     |    Thread-10 |will await stop_event ...
 |moler.runner.asyncio-in-thrd:7f54e1690748     |    Thread-10 |START OF feed(NetworkUpDetector(id:7f54e1690748))
 |moler.runner.asyncio-in-thrd:7f54e1690748     |    Thread-10 |start feeding(NetworkUpDetector(id:7f54e1690748))
 |moler.runner.asyncio-in-thrd:7f54e1690748     |    Thread-10 |feed subscribing for data NetworkUpDetector(id:7f54e1690748, using ObservableConnection(id:7f54e6875ef0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875160>>])
 |moler.runner.asyncio-in-thrd:7f54e1690748     |    Thread-10 |feeding(NetworkUpDetector(id:7f54e1690748)) started
 |moler.runner.asyncio-in-thrd:7f54e1690748     |   MainThread |returning iterator for NetworkUpDetector(id:7f54e1690748)
 |moler.user.app-code                           |   MainThread |Network 10.0.2.16 is back "up" from 13:04:50
 |tcp-thrd-io.net_2                             |   MainThread |connection tcp://localhost:5672 is closed
 |moler.user.app-code                           |   MainThread |exiting ping_observing_task
 |tcp-thrd-io.net_1                             |     Thread-9 |< b'ping: sendmsg: Network is unreachable\n'
 |moler.net_1                                   |     Thread-9 |ping: sendmsg: Network is unreachable

 |tcp-thrd-io.net_1                             |     Thread-9 |< b'ping: sendmsg: Network is unreachable\n'
 |moler.net_1                                   |     Thread-9 |ping: sendmsg: Network is unreachable

 |tcp-thrd-io.net_1                             |     Thread-9 |< b'64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms\n'
 |moler.net_1                                   |     Thread-9 |64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms

 |moler.NetworkUpDetector(id:7f54e1690748)      |     Thread-9 |Network 10.0.2.15 is up!
 |moler.runner.asyncio-in-thrd:7f54e1690748     |    Thread-10 |feed done & unsubscribing NetworkUpDetector(id:7f54e1690748, using ObservableConnection(id:7f54e6875ef0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f54e6875160>>])
 |moler.runner.asyncio-in-thrd:7f54e1690748     |    Thread-10 |feed returning result NetworkUpDetector(id:7f54e1690748)
 |moler.runner.asyncio-in-thrd:7f54e1690748     |    Thread-10 |END   OF feed(NetworkUpDetector(id:7f54e1690748))
 |moler.user.app-code                           |   MainThread |Network 10.0.2.15 is back "up" from 13:04:56
 |tcp-thrd-io.net_1                             |   MainThread |connection tcp://localhost:5671 is closed
 |moler.user.app-code                           |   MainThread |exiting ping_observing_task
 |asyncio.main                                  |   MainThread |after all ping_observing_task
 |asyncio.main                                  |   MainThread |cancelling all remaining tasks
 |asyncio.main                                  |   MainThread |closing events loop ...
 |asyncio.main                                  |   MainThread |... events loop closed
 |threaded.ping.tcp-server(5671)                |     Thread-1 |Ping Sim: ... bye
 |threaded.ping.tcp-server(5672)                |     Thread-2 |Ping Sim: ... bye
 |asyncio                                       |     Thread-6 |poll took 6222.634 ms: 1 events
 |moler.runner.asyncio-in-thrd:7f54e6875668     |     Thread-6 |... await stop_event done
 |moler.runner.asyncio-in-thrd:7f54e6875668     |     Thread-6 |... asyncio-in-thrd loop done
 |threaded.ping.tcp-server(5671 -> 49430)       |     Thread-8 |Connection closed
 |asyncio                                       |    Thread-10 |poll took 1993.816 ms: 1 events
 |moler.runner.asyncio-in-thrd:7f54e1690748     |    Thread-10 |... await stop_event done
 |moler.runner.asyncio-in-thrd:7f54e1690748     |    Thread-10 |... asyncio-in-thrd loop done
 |moler.runner.asyncio-in-thrd:7f54e1690748     |     Dummy-11 |shutting down
 |moler.runner.asyncio-in-thrd:7f54e16906a0     |     Dummy-11 |shutting down
 |moler.runner.asyncio-in-thrd:7f54e6875668     |     Dummy-11 |shutting down
 |moler.runner.asyncio-in-thrd:7f54e6875550     |     Dummy-11 |shutting down
 |asyncio                                       |     Dummy-11 |Close <_UnixSelectorEventLoop running=False closed=False debug=True>
 |asyncio                                       |     Dummy-11 |Close <_UnixSelectorEventLoop running=False closed=False debug=True>
 |asyncio                                       |     Dummy-11 |Close <_UnixSelectorEventLoop running=False closed=False debug=True>
 |asyncio                                       |     Dummy-11 |Close <_UnixSelectorEventLoop running=False closed=False debug=True>
'''
