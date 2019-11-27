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
Best choice here is to use 'asyncio' runner.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import logging
import sys
import os
import time
import asyncio

from moler.connection_factory import get_connection
from moler.runner_factory import get_runner

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
                                            runner=get_runner(variant="asyncio"))
    net_up_detector = NetworkUpDetector(ping_ip,
                                        connection=ext_io_connection.moler_connection,
                                        runner=get_runner(variant="asyncio"))

    info = '{} on {} using {}'.format(ping_ip, conn_addr, net_down_detector)
    logger.debug('observe ' + info)

    # 4. start observer (nonblocking, using as future)
    net_down_detector.start()  # should be started before we open connection
    # to not loose first data on connection

    async with ext_io_connection:
        # 5. await that observer to complete
        try:
            net_down_time = await asyncio.wait_for(net_down_detector, timeout=10)  # =2 --> TimeoutError
            timestamp = time.strftime("%H:%M:%S", time.localtime(net_down_time))
            logger.debug('Network {} is down from {}'.format(ping_ip, timestamp))
        except asyncio.TimeoutError:
            logger.debug('Network down detector timed out')

        # 6. call next observer (blocking till completes)
        info = '{} on {} using {}'.format(ping_ip, conn_addr, net_up_detector)
        logger.debug('observe ' + info)
        # using as synchronous function (so we want verb to express action)
        detect_network_up = net_up_detector
        net_up_time = await detect_network_up  # if you want timeout - see code above
        timestamp = time.strftime("%H:%M:%S", time.localtime(net_up_time))
        logger.debug('Network {} is back "up" from {}'.format(ping_ip, timestamp))
    logger.debug('exiting ping_observing_task({})'.format(ping_ip))


# ==============================================================================
async def main(connections2observe4ip):
    logger = logging.getLogger('asyncio.main')
    logger.debug('starting jobs observing connections')
    # Starting the clients
    jobs_on_connections = []
    for _, connection_name, ping_ip in connections2observe4ip:
        # ------------------------------------------------------------------
        # This front-end code hides all details of connection.
        # We just use its name - such name should be meaningful for user.
        # like: "main_dns_server", "backup_ntp_server", ...
        # Another words, all we want here is stg like:
        # "give me connection to main_dns_server"
        # ------------------------------------------------------------------
        con_logger = logging.getLogger('tcp-async-io.{}'.format(connection_name))
        tcp_connection = get_connection(name=connection_name, variant='asyncio', logger=con_logger)

        # client_task= asyncio.ensure_future(ping_observing_task(tcp_connection, ping_ip))
        jobs_on_connections.append(ping_observing_task(tcp_connection, ping_ip))
    # await observers job to be done
    completed, pending = await asyncio.wait(jobs_on_connections)
    logger.debug('all jobs observing connections are done')


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

15:27:29 |threaded.ping.tcp-server(5671)                |   MainThread |Ping Sim started at tcp://localhost:5671
15:27:29 |threaded.ping.tcp-server(5672)                |   MainThread |Ping Sim started at tcp://localhost:5672
15:27:29 |asyncio                                       |   MainThread |Using selector: EpollSelector
15:27:29 |asyncio.main                                  |   MainThread |starting events loop ...
15:27:29 |asyncio.main                                  |   MainThread |starting jobs observing connections
15:27:29 |moler.runner.asyncio                          |   MainThread |created
15:27:29 |moler.user.app-code                           |   MainThread |observe 10.0.2.16 on tcp://localhost:5672 using NetworkDownDetector(id:7fd69b63eb70)
15:27:29 |moler.runner.asyncio                          |   MainThread |go background: NetworkDownDetector(id:7fd69b63eb70, using ObservableConnection(id:7fd69b63e208)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63eac8>>])
15:27:29 |moler.runner.asyncio                          |   MainThread |start feeding(NetworkDownDetector(id:7fd69b63eb70))
15:27:29 |moler.runner.asyncio                          |   MainThread |feed subscribing for data NetworkDownDetector(id:7fd69b63eb70, using ObservableConnection(id:7fd69b63e208)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63eac8>>])
15:27:29 |moler.runner.asyncio                          |   MainThread |feeding(NetworkDownDetector(id:7fd69b63eb70)) started
15:27:29 |tcp-async-io.net_2                            |   MainThread |connecting to tcp://localhost:5672
15:27:29 |moler.user.app-code                           |   MainThread |observe 10.0.2.15 on tcp://localhost:5671 using NetworkDownDetector(id:7fd69b63ef60)
15:27:29 |moler.runner.asyncio                          |   MainThread |go background: NetworkDownDetector(id:7fd69b63ef60, using ObservableConnection(id:7fd69b63e630)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63e828>>])
15:27:29 |moler.runner.asyncio                          |   MainThread |start feeding(NetworkDownDetector(id:7fd69b63ef60))
15:27:29 |moler.runner.asyncio                          |   MainThread |feed subscribing for data NetworkDownDetector(id:7fd69b63ef60, using ObservableConnection(id:7fd69b63e630)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63e828>>])
15:27:29 |moler.runner.asyncio                          |   MainThread |feeding(NetworkDownDetector(id:7fd69b63ef60)) started
15:27:29 |tcp-async-io.net_1                            |   MainThread |connecting to tcp://localhost:5671
15:27:30 |moler.NetworkDownDetector(id:7fd69b63eb70)    |   MainThread |Observer 'network_toggle_observers.NetworkDownDetector' started.
15:27:30 |moler.net_2                                   |   MainThread |Observer 'network_toggle_observers.NetworkDownDetector' started.
15:27:30 |moler.runner.asyncio                          |   MainThread |START OF feed(NetworkDownDetector(id:7fd69b63eb70))
15:27:30 |moler.NetworkDownDetector(id:7fd69b63ef60)    |   MainThread |Observer 'network_toggle_observers.NetworkDownDetector' started.
15:27:30 |moler.net_1                                   |   MainThread |Observer 'network_toggle_observers.NetworkDownDetector' started.
15:27:30 |moler.runner.asyncio                          |   MainThread |START OF feed(NetworkDownDetector(id:7fd69b63ef60))
15:27:30 |tcp-async-io.net_2                            |   MainThread |connection tcp://localhost:5672 is open
15:27:30 |tcp-async-io.net_1                            |   MainThread |connection tcp://localhost:5671 is open
15:27:30 |moler.runner.asyncio                          |   MainThread |go foreground: NetworkDownDetector(id:7fd69b63eb70, using ObservableConnection(id:7fd69b63e208)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63eac8>>])
15:27:30 |moler.runner.asyncio                          |   MainThread |go foreground: NetworkDownDetector(id:7fd69b63ef60, using ObservableConnection(id:7fd69b63e630)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63e828>>])
15:27:30 |threaded.ping.tcp-server(5672 -> 43371)       |     Thread-3 |connection accepted - client at tcp://127.0.0.1:43371
15:27:30 |tcp-async-io.net_2                            |   MainThread |< b'\n'
15:27:30 |moler.net_2                                   |   MainThread |

15:27:30 |threaded.ping.tcp-server(5671 -> 49569)       |     Thread-4 |connection accepted - client at tcp://127.0.0.1:49569
15:27:30 |tcp-async-io.net_1                            |   MainThread |< b'\n'
15:27:30 |moler.net_1                                   |   MainThread |

15:27:31 |tcp-async-io.net_2                            |   MainThread |< b'greg@debian:~$ ping 10.0.2.16\n'
15:27:31 |moler.net_2                                   |   MainThread |greg@debian:~$ ping 10.0.2.16

15:27:31 |tcp-async-io.net_1                            |   MainThread |< b'greg@debian:~$ ping 10.0.2.15\n'
15:27:31 |moler.net_1                                   |   MainThread |greg@debian:~$ ping 10.0.2.15

15:27:32 |tcp-async-io.net_2                            |   MainThread |< b'PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.\n'
15:27:32 |moler.net_2                                   |   MainThread |PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.

15:27:32 |tcp-async-io.net_1                            |   MainThread |< b'PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.\n'
15:27:32 |moler.net_1                                   |   MainThread |PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.

15:27:33 |tcp-async-io.net_2                            |   MainThread |< b'64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms\n'
15:27:33 |moler.net_2                                   |   MainThread |64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms

15:27:33 |tcp-async-io.net_1                            |   MainThread |< b'64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms\n'
15:27:33 |moler.net_1                                   |   MainThread |64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms

15:27:34 |tcp-async-io.net_2                            |   MainThread |< b'64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms\n'
15:27:34 |moler.net_2                                   |   MainThread |64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms

15:27:34 |tcp-async-io.net_1                            |   MainThread |< b'64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms\n'
15:27:34 |moler.net_1                                   |   MainThread |64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms

15:27:35 |tcp-async-io.net_2                            |   MainThread |< b'64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms\n'
15:27:35 |moler.net_2                                   |   MainThread |64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms

15:27:35 |tcp-async-io.net_1                            |   MainThread |< b'64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms\n'
15:27:35 |moler.net_1                                   |   MainThread |64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms

15:27:36 |tcp-async-io.net_2                            |   MainThread |< b'ping: sendmsg: Network is unreachable\n'
15:27:36 |moler.net_2                                   |   MainThread |ping: sendmsg: Network is unreachable

15:27:36 |moler.NetworkDownDetector(id:7fd69b63eb70)    |   MainThread |Network 10.0.2.16 is down!
15:27:36 |tcp-async-io.net_1                            |   MainThread |< b'ping: sendmsg: Network is unreachable\n'
15:27:36 |moler.net_1                                   |   MainThread |ping: sendmsg: Network is unreachable

15:27:36 |moler.NetworkDownDetector(id:7fd69b63ef60)    |   MainThread |Network 10.0.2.15 is down!
15:27:36 |moler.runner.asyncio                          |   MainThread |feed done & unsubscribing NetworkDownDetector(id:7fd69b63eb70, using ObservableConnection(id:7fd69b63e208)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63eac8>>])
15:27:36 |moler.runner.asyncio                          |   MainThread |END   OF feed(NetworkDownDetector(id:7fd69b63eb70))
15:27:36 |moler.runner.asyncio                          |   MainThread |feed returning result: 1541514456.0239358
15:27:36 |moler.NetworkDownDetector(id:7fd69b63eb70)    |   MainThread |Observer 'network_toggle_observers.NetworkDownDetector' finished.
15:27:36 |moler.net_2                                   |   MainThread |Observer 'network_toggle_observers.NetworkDownDetector' finished.
15:27:36 |moler.runner.asyncio                          |   MainThread |feed done & unsubscribing NetworkDownDetector(id:7fd69b63ef60, using ObservableConnection(id:7fd69b63e630)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63e828>>])
15:27:36 |moler.runner.asyncio                          |   MainThread |END   OF feed(NetworkDownDetector(id:7fd69b63ef60))
15:27:36 |moler.runner.asyncio                          |   MainThread |feed returning result: 1541514456.0241282
15:27:36 |moler.NetworkDownDetector(id:7fd69b63ef60)    |   MainThread |Observer 'network_toggle_observers.NetworkDownDetector' finished.
15:27:36 |moler.net_1                                   |   MainThread |Observer 'network_toggle_observers.NetworkDownDetector' finished.
15:27:36 |moler.user.app-code                           |   MainThread |Network 10.0.2.16 is down from 15:27:36
15:27:36 |moler.user.app-code                           |   MainThread |observe 10.0.2.16 on tcp://localhost:5672 using NetworkUpDetector(id:7fd69b63ed68)
15:27:36 |moler.runner.asyncio                          |   MainThread |go background: NetworkUpDetector(id:7fd69b63ed68, using ObservableConnection(id:7fd69b63e208)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63eac8>>])
15:27:36 |moler.runner.asyncio                          |   MainThread |start feeding(NetworkUpDetector(id:7fd69b63ed68))
15:27:36 |moler.runner.asyncio                          |   MainThread |feed subscribing for data NetworkUpDetector(id:7fd69b63ed68, using ObservableConnection(id:7fd69b63e208)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63eac8>>])
15:27:36 |moler.runner.asyncio                          |   MainThread |feeding(NetworkUpDetector(id:7fd69b63ed68)) started
15:27:36 |moler.runner.asyncio                          |   MainThread |go foreground: NetworkUpDetector(id:7fd69b63ed68, using ObservableConnection(id:7fd69b63e208)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63eac8>>])
15:27:36 |moler.user.app-code                           |   MainThread |Network 10.0.2.15 is down from 15:27:36
15:27:36 |moler.user.app-code                           |   MainThread |observe 10.0.2.15 on tcp://localhost:5671 using NetworkUpDetector(id:7fd69b664048)
15:27:36 |moler.runner.asyncio                          |   MainThread |go background: NetworkUpDetector(id:7fd69b664048, using ObservableConnection(id:7fd69b63e630)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63e828>>])
15:27:36 |moler.runner.asyncio                          |   MainThread |start feeding(NetworkUpDetector(id:7fd69b664048))
15:27:36 |moler.runner.asyncio                          |   MainThread |feed subscribing for data NetworkUpDetector(id:7fd69b664048, using ObservableConnection(id:7fd69b63e630)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63e828>>])
15:27:36 |moler.runner.asyncio                          |   MainThread |feeding(NetworkUpDetector(id:7fd69b664048)) started
15:27:36 |moler.runner.asyncio                          |   MainThread |go foreground: NetworkUpDetector(id:7fd69b664048, using ObservableConnection(id:7fd69b63e630)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63e828>>])
15:27:36 |moler.NetworkUpDetector(id:7fd69b63ed68)      |   MainThread |Observer 'network_toggle_observers.NetworkUpDetector' started.
15:27:36 |moler.net_2                                   |   MainThread |Observer 'network_toggle_observers.NetworkUpDetector' started.
15:27:36 |moler.runner.asyncio                          |   MainThread |START OF feed(NetworkUpDetector(id:7fd69b63ed68))
15:27:36 |moler.NetworkUpDetector(id:7fd69b664048)      |   MainThread |Observer 'network_toggle_observers.NetworkUpDetector' started.
15:27:36 |moler.net_1                                   |   MainThread |Observer 'network_toggle_observers.NetworkUpDetector' started.
15:27:36 |moler.runner.asyncio                          |   MainThread |START OF feed(NetworkUpDetector(id:7fd69b664048))
15:27:37 |tcp-async-io.net_2                            |   MainThread |< b'ping: sendmsg: Network is unreachable\n'
15:27:37 |moler.net_2                                   |   MainThread |ping: sendmsg: Network is unreachable

15:27:37 |tcp-async-io.net_1                            |   MainThread |< b'ping: sendmsg: Network is unreachable\n'
15:27:37 |moler.net_1                                   |   MainThread |ping: sendmsg: Network is unreachable

15:27:38 |tcp-async-io.net_2                            |   MainThread |< b'ping: sendmsg: Network is unreachable\n'
15:27:38 |moler.net_2                                   |   MainThread |ping: sendmsg: Network is unreachable

15:27:38 |tcp-async-io.net_1                            |   MainThread |< b'ping: sendmsg: Network is unreachable\n'
15:27:38 |moler.net_1                                   |   MainThread |ping: sendmsg: Network is unreachable

15:27:39 |tcp-async-io.net_2                            |   MainThread |< b'64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms\n'
15:27:39 |moler.net_2                                   |   MainThread |64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms

15:27:39 |moler.NetworkUpDetector(id:7fd69b63ed68)      |   MainThread |Network 10.0.2.16 is up!
15:27:39 |tcp-async-io.net_1                            |   MainThread |< b'64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms\n'
15:27:39 |moler.net_1                                   |   MainThread |64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms

15:27:39 |moler.NetworkUpDetector(id:7fd69b664048)      |   MainThread |Network 10.0.2.15 is up!
15:27:39 |moler.runner.asyncio                          |   MainThread |feed done & unsubscribing NetworkUpDetector(id:7fd69b63ed68, using ObservableConnection(id:7fd69b63e208)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63eac8>>])
15:27:39 |moler.runner.asyncio                          |   MainThread |END   OF feed(NetworkUpDetector(id:7fd69b63ed68))
15:27:39 |moler.runner.asyncio                          |   MainThread |feed returning result: 1541514459.0279741
15:27:39 |moler.NetworkUpDetector(id:7fd69b63ed68)      |   MainThread |Observer 'network_toggle_observers.NetworkUpDetector' finished.
15:27:39 |moler.net_2                                   |   MainThread |Observer 'network_toggle_observers.NetworkUpDetector' finished.
15:27:39 |moler.runner.asyncio                          |   MainThread |feed done & unsubscribing NetworkUpDetector(id:7fd69b664048, using ObservableConnection(id:7fd69b63e630)-->[<bound method AsyncioTcp._send of <moler.io.asyncio.tcp.AsyncioTcp object at 0x7fd69b63e828>>])
15:27:39 |moler.runner.asyncio                          |   MainThread |END   OF feed(NetworkUpDetector(id:7fd69b664048))
15:27:39 |moler.runner.asyncio                          |   MainThread |feed returning result: 1541514459.0282097
15:27:39 |moler.NetworkUpDetector(id:7fd69b664048)      |   MainThread |Observer 'network_toggle_observers.NetworkUpDetector' finished.
15:27:39 |moler.net_1                                   |   MainThread |Observer 'network_toggle_observers.NetworkUpDetector' finished.
15:27:39 |moler.user.app-code                           |   MainThread |Network 10.0.2.16 is back "up" from 15:27:39
15:27:39 |tcp-async-io.net_2                            |   MainThread |closing tcp://localhost:5672
15:27:39 |moler.user.app-code                           |   MainThread |Network 10.0.2.15 is back "up" from 15:27:39
15:27:39 |tcp-async-io.net_1                            |   MainThread |closing tcp://localhost:5671
15:27:39 |tcp-async-io.net_2                            |   MainThread |connection tcp://localhost:5672 is closed
15:27:39 |moler.user.app-code                           |   MainThread |exiting ping_observing_task(10.0.2.16)
15:27:39 |tcp-async-io.net_1                            |   MainThread |connection tcp://localhost:5671 is closed
15:27:39 |moler.user.app-code                           |   MainThread |exiting ping_observing_task(10.0.2.15)
15:27:39 |asyncio.main                                  |   MainThread |all jobs observing connections are done
15:27:39 |asyncio.main                                  |   MainThread |cancelling all remaining tasks
15:27:39 |asyncio.main                                  |   MainThread |closing events loop ...
15:27:39 |asyncio.main                                  |   MainThread |... events loop closed
15:27:39 |threaded.ping.tcp-server(5671)                |     Thread-1 |Ping Sim: ... bye
15:27:39 |threaded.ping.tcp-server(5672)                |     Thread-2 |Ping Sim: ... bye
15:27:41 |threaded.ping.tcp-server(5672 -> 43371)       |     Thread-3 |Connection closed
15:27:41 |threaded.ping.tcp-server(5671 -> 49569)       |     Thread-4 |Connection closed
15:27:41 |moler.runner.asyncio                          |      Dummy-5 |shutting down
'''
