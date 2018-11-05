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
Best choice here is to use 'asyncio-in-thread' runner.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import logging
import sys
import os
import threading
import time
import asyncio

from moler.connection import get_connection
from moler.runner_factory import get_runner
from moler.asyncio_runner import AsyncioInThreadRunner

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))  # allow finding modules in examples/

from network_toggle_observers import NetworkDownDetector, NetworkUpDetector


# ===================== Moler's connection-observer usage ======================


def ping_observing_task(ext_io_connection, ping_ip):
    """
    Here external-IO connection is abstract - we don't know its type.
    What we know is just that it has .moler_connection attribute.
    """
    # asyncio's policy:
    # You must create an event loop explicitly for each thread
    asyncio.set_event_loop(asyncio.new_event_loop())

    logger = logging.getLogger('moler.user.app-code')
    conn_addr = str(ext_io_connection)

    # Layer 2 of Moler's usage (ext_io_connection + runner):
    # 3. create observers on Moler's connection
    net_down_detector = NetworkDownDetector(ping_ip,
                                            connection=ext_io_connection.moler_connection,
                                            runner=AsyncioInThreadRunner())  # get_runner(variant="asyncio-in-thread"))
    net_up_detector = NetworkUpDetector(ping_ip,
                                        connection=ext_io_connection.moler_connection,
                                        runner=AsyncioInThreadRunner())  # get_runner(variant="asyncio-in-thread"))

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
        tcp_connection = get_connection(name=connection_name)
        # con_logger = logging.getLogger('tcp-async_in_thrd-io.{}'.format(connection_name))
        # tcp_connection = get_connection(name=connection_name, variant='asyncio-in-thread', logger=con_logger)
        tcp_connection.moler_connection.name = connection_name
        client_thread = threading.Thread(target=ping_observing_task,
                                         args=(tcp_connection, ping_ip))
        client_thread.start()
        jobs_on_connections.append(client_thread)
    # await observers job to be done
    for client_thread in jobs_on_connections:
        client_thread.join()
    logger.debug('all jobs observing connections are done')


# ==============================================================================
if __name__ == '__main__':
    from threaded_ping_server import start_ping_servers, stop_ping_servers
    from asyncio_common import configure_logging
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
        main(connections2observe4ip)
    finally:
        stop_ping_servers(servers)

'''
LOG OUTPUT

 |threaded.ping.tcp-server(5671)                |   MainThread |Ping Sim started at tcp://localhost:5671
 |threaded.ping.tcp-server(5672)                |   MainThread |Ping Sim started at tcp://localhost:5672
 |asyncio                                       |     Thread-3 |Using selector: EpollSelector
 |moler.runner.asyncio-in-thrd:0                |     Thread-3 |created
 |moler.runner.asyncio-in-thrd:0                |     Thread-3 |created
 |moler.user.app-code                           |     Thread-3 |observe 10.0.2.15 on tcp://localhost:5671 using NetworkDownDetector(id:7f2a774fb358)
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-3 |go background: NetworkDownDetector(id:7f2a774fb358, using ObservableConnection(id:7f2a774e9be0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774e9e48>>])
 |asyncio                                       |     Thread-3 |Using selector: EpollSelector
 |asyncio                                       |     Thread-4 |Using selector: EpollSelector
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-5 |starting new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-3 |started new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:0                |     Thread-4 |created
 |moler.runner.asyncio-in-thrd:0                |     Thread-4 |created
 |moler.user.app-code                           |     Thread-4 |observe 10.0.2.16 on tcp://localhost:5672 using NetworkDownDetector(id:7f2a7131f0b8)
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-4 |go background: NetworkDownDetector(id:7f2a7131f0b8, using ObservableConnection(id:7f2a774fb588)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774fb5c0>>])
 |asyncio                                       |     Thread-4 |Using selector: EpollSelector
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-5 |will await stop_event ...
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-5 |START OF feed(NetworkDownDetector(id:7f2a774fb358))
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-5 |start feeding(NetworkDownDetector(id:7f2a774fb358))
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-5 |feed subscribing for data NetworkDownDetector(id:7f2a774fb358, using ObservableConnection(id:7f2a774e9be0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774e9e48>>])
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-5 |feeding(NetworkDownDetector(id:7f2a774fb358)) started
 |threaded.ping.tcp-server(5671 -> 49439)       |     Thread-7 |connection accepted - client at tcp://127.0.0.1:49439
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-6 |starting new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-6 |will await stop_event ...
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-4 |started new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-6 |START OF feed(NetworkDownDetector(id:7f2a7131f0b8))
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-6 |start feeding(NetworkDownDetector(id:7f2a7131f0b8))
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-6 |feed subscribing for data NetworkDownDetector(id:7f2a7131f0b8, using ObservableConnection(id:7f2a774fb588)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774fb5c0>>])
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-6 |feeding(NetworkDownDetector(id:7f2a7131f0b8)) started
 |moler.net_1                                   |     Thread-8 |

 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-3 |go foreground: NetworkDownDetector(id:7f2a774fb358, using ObservableConnection(id:7f2a774e9be0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774e9e48>>]) - await max. 10 [sec]
 |threaded.ping.tcp-server(5672 -> 43243)       |    Thread-10 |connection accepted - client at tcp://127.0.0.1:43243
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-4 |go foreground: NetworkDownDetector(id:7f2a7131f0b8, using ObservableConnection(id:7f2a774fb588)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774fb5c0>>]) - await max. 10 [sec]
 |moler.net_2                                   |     Thread-9 |

 |moler.net_1                                   |     Thread-8 |greg@debian:~$ ping 10.0.2.15

 |moler.net_2                                   |     Thread-9 |greg@debian:~$ ping 10.0.2.16

 |moler.net_1                                   |     Thread-8 |PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.

 |moler.net_2                                   |     Thread-9 |PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.

 |moler.net_1                                   |     Thread-8 |64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms

 |moler.net_2                                   |     Thread-9 |64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms

 |moler.net_1                                   |     Thread-8 |64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms

 |moler.net_2                                   |     Thread-9 |64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms

 |moler.net_1                                   |     Thread-8 |64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms

 |moler.net_2                                   |     Thread-9 |64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms

 |moler.net_1                                   |     Thread-8 |ping: sendmsg: Network is unreachable

 |moler.NetworkDownDetector(id:7f2a774fb358)    |     Thread-8 |Network 10.0.2.15 is down!
 |moler.net_2                                   |     Thread-9 |ping: sendmsg: Network is unreachable

 |moler.NetworkDownDetector(id:7f2a7131f0b8)    |     Thread-9 |Network 10.0.2.16 is down!
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-6 |feed done & unsubscribing NetworkDownDetector(id:7f2a7131f0b8, using ObservableConnection(id:7f2a774fb588)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774fb5c0>>])
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-6 |feed returning result NetworkDownDetector(id:7f2a7131f0b8)
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-6 |END   OF feed(NetworkDownDetector(id:7f2a7131f0b8))
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-4 |shutting down
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-4 |NetworkDownDetector(id:7f2a7131f0b8) returned 1541419711.0872927
 |moler.user.app-code                           |     Thread-4 |Network 10.0.2.16 is down from 13:08:31
 |moler.user.app-code                           |     Thread-4 |observe 10.0.2.16 on tcp://localhost:5672 using NetworkUpDetector(id:7f2a7131f160)
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |     Thread-4 |go background: NetworkUpDetector(id:7f2a7131f160, using ObservableConnection(id:7f2a774fb588)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774fb5c0>>])
 |asyncio                                       |     Thread-4 |Using selector: EpollSelector
 |asyncio                                       |     Thread-6 |poll took 1.135 ms: 1 events
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-6 |... await stop_event done
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Thread-6 |... asyncio-in-thrd loop done
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-5 |feed done & unsubscribing NetworkDownDetector(id:7f2a774fb358, using ObservableConnection(id:7f2a774e9be0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774e9e48>>])
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-5 |feed returning result NetworkDownDetector(id:7f2a774fb358)
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-5 |END   OF feed(NetworkDownDetector(id:7f2a774fb358))
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-3 |shutting down
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-3 |NetworkDownDetector(id:7f2a774fb358) returned 1541419711.087151
 |moler.user.app-code                           |     Thread-3 |Network 10.0.2.15 is down from 13:08:31
 |moler.user.app-code                           |     Thread-3 |observe 10.0.2.15 on tcp://localhost:5671 using NetworkUpDetector(id:7f2a774fb208)
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |     Thread-3 |go background: NetworkUpDetector(id:7f2a774fb208, using ObservableConnection(id:7f2a774e9be0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774e9e48>>])
 |asyncio                                       |     Thread-3 |Using selector: EpollSelector
 |asyncio                                       |     Thread-5 |poll took 1.268 ms: 1 events
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |    Thread-11 |starting new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |    Thread-11 |will await stop_event ...
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |     Thread-4 |started new asyncio-in-thrd loop ...
 |asyncio                                       |    Thread-11 |poll took 0.428 ms: 1 events
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-5 |... await stop_event done
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |    Thread-11 |START OF feed(NetworkUpDetector(id:7f2a7131f160))
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |    Thread-11 |start feeding(NetworkUpDetector(id:7f2a7131f160))
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |    Thread-11 |feed subscribing for data NetworkUpDetector(id:7f2a7131f160, using ObservableConnection(id:7f2a774fb588)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774fb5c0>>])
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |    Thread-11 |feeding(NetworkUpDetector(id:7f2a7131f160)) started
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |     Thread-4 |go foreground: NetworkUpDetector(id:7f2a7131f160, using ObservableConnection(id:7f2a774fb588)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774fb5c0>>]) - await max. None [sec]
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Thread-5 |... asyncio-in-thrd loop done
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |    Thread-12 |starting new asyncio-in-thrd loop ...
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |    Thread-12 |will await stop_event ...
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |     Thread-3 |started new asyncio-in-thrd loop ...
 |asyncio                                       |    Thread-12 |poll took 0.317 ms: 1 events
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |    Thread-12 |START OF feed(NetworkUpDetector(id:7f2a774fb208))
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |    Thread-12 |start feeding(NetworkUpDetector(id:7f2a774fb208))
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |    Thread-12 |feed subscribing for data NetworkUpDetector(id:7f2a774fb208, using ObservableConnection(id:7f2a774e9be0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774e9e48>>])
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |    Thread-12 |feeding(NetworkUpDetector(id:7f2a774fb208)) started
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |     Thread-3 |go foreground: NetworkUpDetector(id:7f2a774fb208, using ObservableConnection(id:7f2a774e9be0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774e9e48>>]) - await max. None [sec]
 |moler.net_1                                   |     Thread-8 |ping: sendmsg: Network is unreachable

 |moler.net_2                                   |     Thread-9 |ping: sendmsg: Network is unreachable

 |moler.net_1                                   |     Thread-8 |ping: sendmsg: Network is unreachable

 |moler.net_2                                   |     Thread-9 |ping: sendmsg: Network is unreachable

 |moler.net_1                                   |     Thread-8 |64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms

 |moler.NetworkUpDetector(id:7f2a774fb208)      |     Thread-8 |Network 10.0.2.15 is up!
 |moler.net_2                                   |     Thread-9 |64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms

 |moler.NetworkUpDetector(id:7f2a7131f160)      |     Thread-9 |Network 10.0.2.16 is up!
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |    Thread-11 |feed done & unsubscribing NetworkUpDetector(id:7f2a7131f160, using ObservableConnection(id:7f2a774fb588)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774fb5c0>>])
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |    Thread-11 |feed returning result NetworkUpDetector(id:7f2a7131f160)
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |    Thread-11 |END   OF feed(NetworkUpDetector(id:7f2a7131f160))
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |    Thread-12 |feed done & unsubscribing NetworkUpDetector(id:7f2a774fb208, using ObservableConnection(id:7f2a774e9be0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f2a774e9e48>>])
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |    Thread-12 |feed returning result NetworkUpDetector(id:7f2a774fb208)
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |    Thread-12 |END   OF feed(NetworkUpDetector(id:7f2a774fb208))
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |     Thread-3 |shutting down
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |     Thread-3 |NetworkUpDetector(id:7f2a774fb208) returned 1541419714.092892
 |moler.user.app-code                           |     Thread-3 |Network 10.0.2.15 is back "up" from 13:08:34
 |asyncio                                       |    Thread-12 |poll took 0.486 ms: 1 events
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |    Thread-12 |... await stop_event done
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |    Thread-12 |... asyncio-in-thrd loop done
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |     Thread-4 |shutting down
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |     Thread-4 |NetworkUpDetector(id:7f2a7131f160) returned 1541419714.0949519
 |moler.user.app-code                           |     Thread-4 |Network 10.0.2.16 is back "up" from 13:08:34
 |asyncio                                       |    Thread-11 |poll took 3.366 ms: 1 events
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |    Thread-11 |... await stop_event done
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |    Thread-11 |... asyncio-in-thrd loop done
 |threaded.ping.tcp-server(5671)                |     Thread-1 |Ping Sim: ... bye
 |threaded.ping.tcp-server(5672)                |     Thread-2 |Ping Sim: ... bye
 |threaded.ping.tcp-server(5671 -> 49439)       |     Thread-7 |Connection closed
 |threaded.ping.tcp-server(5672 -> 43243)       |    Thread-10 |Connection closed
 |moler.runner.asyncio-in-thrd:7f2a7131f160     |     Dummy-13 |shutting down
 |moler.runner.asyncio-in-thrd:7f2a7131f0b8     |     Dummy-13 |shutting down
 |moler.runner.asyncio-in-thrd:7f2a774fb208     |     Dummy-13 |shutting down
 |moler.runner.asyncio-in-thrd:7f2a774fb358     |     Dummy-13 |shutting down
 |asyncio                                       |     Dummy-13 |Close <_UnixSelectorEventLoop running=False closed=False debug=True>
 |asyncio                                       |     Dummy-13 |Close <_UnixSelectorEventLoop running=False closed=False debug=True>
 |asyncio                                       |     Dummy-13 |Close <_UnixSelectorEventLoop running=False closed=False debug=True>
 |asyncio                                       |     Dummy-13 |Close <_UnixSelectorEventLoop running=False closed=False debug=True>
'''
