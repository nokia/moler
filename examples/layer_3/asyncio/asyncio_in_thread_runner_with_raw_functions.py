# -*- coding: utf-8 -*-
"""
asyncio_in_thread_runner_with_raw_functions.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

from moler.connection import get_connection
from moler.exceptions import ConnectionObserverTimeout
from moler.runner_factory import get_runner

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
    net_down_detector = NetworkDownDetector(ping_ip,
                                            connection=ext_io_connection.moler_connection,
                                            runner=get_runner(variant="asyncio-in-thread"))
    net_up_detector = NetworkUpDetector(ping_ip,
                                        connection=ext_io_connection.moler_connection,
                                        runner=get_runner(variant="asyncio-in-thread"))

    info = '{} on {} using {}'.format(ping_ip, conn_addr, net_down_detector)
    logger.debug('observe ' + info)

    # 4. start observer (nonblocking, using as future)
    net_down_detector.start()  # should be started before we open connection
    # to not loose first data on connection

    with ext_io_connection:
        # 5. await that observer to complete
        try:
            net_down_time = net_down_detector.await_done(timeout=10)  # =2 --> TimeoutError
            timestamp = time.strftime("%H:%M:%S", time.localtime(net_down_time))
            logger.debug('Network {} is down from {}'.format(ping_ip, timestamp))
        except ConnectionObserverTimeout:
            logger.debug('Network down detector timed out')

        # 6. call next observer (blocking till completes)
        info = '{} on {} using {}'.format(ping_ip, conn_addr, net_up_detector)
        logger.debug('observe ' + info)
        # using as synchronous function (so we want verb to express action)
        detect_network_up = net_up_detector
        net_up_time = detect_network_up()  # if you want timeout - see code above
        timestamp = time.strftime("%H:%M:%S", time.localtime(net_up_time))
        logger.debug('Network {} is back "up" from {}'.format(ping_ip, timestamp))
    logger.debug('exiting ping_observing_task({})'.format(ping_ip))


# ==============================================================================
def main(connections2observe4ip):
    logger = logging.getLogger('asyncio.main')
    logger.debug('starting jobs observing connections')
    # Starting the clients
    jobs_on_connections = []
    for connection_name, ping_ip in connections2observe4ip:
        # ------------------------------------------------------------------
        # This front-end code hides all details of connection.
        # We just use its name - such name should be meaningful for user.
        # like: "main_dns_server", "backup_ntp_server", ...
        # Another words, all we want here is stg like:
        # "give me connection to main_dns_server"
        # ------------------------------------------------------------------
        # con_logger = logging.getLogger('tcp-async_in_thrd-io.{}'.format(connection_name))
        # tcp_connection = get_connection(name=connection_name, variant='asyncio-in-thread', logger=con_logger)
        tcp_connection = get_connection(name=connection_name, variant='asyncio-in-thread')
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

    net_1 = ('localhost', 5671)
    net_2 = ('localhost', 5672)
    connections2serve = [(net_1, '10.0.2.15'),
                         (net_2, '10.0.2.16')]
    connections2observe4ip = [('net_1', '10.0.2.15'),
                              ('net_2', '10.0.2.16')]
    servers = start_ping_servers(connections2serve)
    try:
        main(connections2observe4ip)
    finally:
        stop_ping_servers(servers)

'''
LOG OUTPUT

15:28:23 |threaded.ping.tcp-server(5671)                |   MainThread |Ping Sim started at tcp://localhost:5671
15:28:23 |threaded.ping.tcp-server(5672)                |   MainThread |Ping Sim started at tcp://localhost:5672
15:28:23 |asyncio.main                                  |   MainThread |starting jobs observing connections
15:28:23 |moler.runner.asyncio-in-thrd:0                |     Thread-3 |created AsyncioInThreadRunner:139990601181112
15:28:23 |moler.user.app-code                           |     Thread-3 |observe 10.0.2.15 on tcp://localhost:5671 using NetworkDownDetector(id:7f521a0e27f0)
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0e27f0     |     Thread-3 |go background: NetworkDownDetector(id:7f521a0e27f0, using ObservableConnection(id:7f521a0e2470)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2630>>])
15:28:23 |asyncio                                       |     Thread-3 |Using selector: EpollSelector
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0e27f0     |     Thread-3 |created loop 4 thread: 139990601182008:<_UnixSelectorEventLoop running=False closed=False debug=False>
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0e27f0     |     Thread-3 |created thread <TillDoneThread(Thread-5, initial)> with loop 139990601182008:<_UnixSelectorEventLoop running=False closed=False debug=True>
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0e27f0     |     Thread-5 |starting new asyncio-in-thrd loop ...
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0e27f0     |     Thread-3 |started new asyncio-in-thrd loop ...
15:28:23 |moler.user.app-code                           |     Thread-4 |observe 10.0.2.16 on tcp://localhost:5672 using NetworkDownDetector(id:7f521a0d6710)
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-4 |go background: NetworkDownDetector(id:7f521a0d6710, using ObservableConnection(id:7f521a0e2780)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2978>>])
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |will await stop_event ...
15:28:23 |moler.NetworkDownDetector(id:7f521a0d6710)    |     Thread-5 |Observer 'network_toggle_observers.NetworkDownDetector' started.
15:28:23 |moler.net_2                                   |     Thread-5 |Observer 'network_toggle_observers.NetworkDownDetector' started.
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |START OF feed(NetworkDownDetector(id:7f521a0d6710))
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |start feeding(NetworkDownDetector(id:7f521a0d6710))
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |feed subscribing for data NetworkDownDetector(id:7f521a0d6710, using ObservableConnection(id:7f521a0e2780)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2978>>])
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |feeding(NetworkDownDetector(id:7f521a0d6710)) started
15:28:23 |moler.NetworkDownDetector(id:7f521a0e27f0)    |     Thread-5 |Observer 'network_toggle_observers.NetworkDownDetector' started.
15:28:23 |moler.net_1                                   |     Thread-5 |Observer 'network_toggle_observers.NetworkDownDetector' started.
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |START OF feed(NetworkDownDetector(id:7f521a0e27f0))
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |start feeding(NetworkDownDetector(id:7f521a0e27f0))
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |feed subscribing for data NetworkDownDetector(id:7f521a0e27f0, using ObservableConnection(id:7f521a0e2470)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2630>>])
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |feeding(NetworkDownDetector(id:7f521a0e27f0)) started
15:28:23 |threaded.ping.tcp-server(5672 -> 43373)       |     Thread-6 |connection accepted - client at tcp://127.0.0.1:43373
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-4 |go foreground: NetworkDownDetector(id:7f521a0d6710, using ObservableConnection(id:7f521a0e2780)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2978>>]) - await max. 10 [sec]
15:28:23 |moler.net_2                                   |     Thread-7 |

15:28:23 |threaded.ping.tcp-server(5671 -> 49571)       |     Thread-8 |connection accepted - client at tcp://127.0.0.1:49571
15:28:23 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-3 |go foreground: NetworkDownDetector(id:7f521a0e27f0, using ObservableConnection(id:7f521a0e2470)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2630>>]) - await max. 10 [sec]
15:28:23 |moler.net_1                                   |     Thread-9 |

15:28:24 |moler.net_2                                   |     Thread-7 |greg@debian:~$ ping 10.0.2.16

15:28:24 |moler.net_1                                   |     Thread-9 |greg@debian:~$ ping 10.0.2.15

15:28:25 |moler.net_2                                   |     Thread-7 |PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.

15:28:25 |moler.net_1                                   |     Thread-9 |PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.

15:28:26 |moler.net_2                                   |     Thread-7 |64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms

15:28:26 |moler.net_1                                   |     Thread-9 |64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms

15:28:27 |moler.net_2                                   |     Thread-7 |64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms

15:28:27 |moler.net_1                                   |     Thread-9 |64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms

15:28:28 |moler.net_2                                   |     Thread-7 |64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms

15:28:28 |moler.net_1                                   |     Thread-9 |64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms

15:28:29 |moler.net_2                                   |     Thread-7 |ping: sendmsg: Network is unreachable

15:28:29 |moler.NetworkDownDetector(id:7f521a0d6710)    |     Thread-7 |Network 10.0.2.16 is down!
15:28:29 |moler.net_1                                   |     Thread-9 |ping: sendmsg: Network is unreachable

15:28:29 |moler.NetworkDownDetector(id:7f521a0e27f0)    |     Thread-9 |Network 10.0.2.15 is down!
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |feed done & unsubscribing NetworkDownDetector(id:7f521a0d6710, using ObservableConnection(id:7f521a0e2780)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2978>>])
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |END   OF feed(NetworkDownDetector(id:7f521a0d6710))
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |feed returning result: 1541514509.3102295
15:28:29 |moler.NetworkDownDetector(id:7f521a0d6710)    |     Thread-5 |Observer 'network_toggle_observers.NetworkDownDetector' finished.
15:28:29 |moler.net_2                                   |     Thread-5 |Observer 'network_toggle_observers.NetworkDownDetector' finished.
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |feed done & unsubscribing NetworkDownDetector(id:7f521a0e27f0, using ObservableConnection(id:7f521a0e2470)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2630>>])
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |END   OF feed(NetworkDownDetector(id:7f521a0e27f0))
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-5 |feed returning result: 1541514509.311799
15:28:29 |moler.NetworkDownDetector(id:7f521a0e27f0)    |     Thread-5 |Observer 'network_toggle_observers.NetworkDownDetector' finished.
15:28:29 |moler.net_1                                   |     Thread-5 |Observer 'network_toggle_observers.NetworkDownDetector' finished.
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6710     |     Thread-3 |NetworkDownDetector(id:7f521a0e27f0) returned 1541514509.311799
15:28:29 |moler.user.app-code                           |     Thread-3 |Network 10.0.2.15 is down from 15:28:29
15:28:29 |moler.user.app-code                           |     Thread-3 |observe 10.0.2.15 on tcp://localhost:5671 using NetworkUpDetector(id:7f521a0e2ba8)
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0e2ba8     |     Thread-3 |go background: NetworkUpDetector(id:7f521a0e2ba8, using ObservableConnection(id:7f521a0e2470)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2630>>])
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0e2ba8     |     Thread-4 |NetworkDownDetector(id:7f521a0d6710) returned 1541514509.3102295
15:28:29 |moler.user.app-code                           |     Thread-4 |Network 10.0.2.16 is down from 15:28:29
15:28:29 |moler.user.app-code                           |     Thread-4 |observe 10.0.2.16 on tcp://localhost:5672 using NetworkUpDetector(id:7f521a0d6860)
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-4 |go background: NetworkUpDetector(id:7f521a0d6860, using ObservableConnection(id:7f521a0e2780)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2978>>])
15:28:29 |asyncio                                       |     Thread-5 |poll took 1.560 ms: 1 events
15:28:29 |moler.NetworkUpDetector(id:7f521a0e2ba8)      |     Thread-5 |Observer 'network_toggle_observers.NetworkUpDetector' started.
15:28:29 |moler.net_1                                   |     Thread-5 |Observer 'network_toggle_observers.NetworkUpDetector' started.
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |START OF feed(NetworkUpDetector(id:7f521a0e2ba8))
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |start feeding(NetworkUpDetector(id:7f521a0e2ba8))
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |feed subscribing for data NetworkUpDetector(id:7f521a0e2ba8, using ObservableConnection(id:7f521a0e2470)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2630>>])
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |feeding(NetworkUpDetector(id:7f521a0e2ba8)) started
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-3 |go foreground: NetworkUpDetector(id:7f521a0e2ba8, using ObservableConnection(id:7f521a0e2470)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2630>>]) - await max. None [sec]
15:28:29 |moler.NetworkUpDetector(id:7f521a0d6860)      |     Thread-5 |Observer 'network_toggle_observers.NetworkUpDetector' started.
15:28:29 |moler.net_2                                   |     Thread-5 |Observer 'network_toggle_observers.NetworkUpDetector' started.
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |START OF feed(NetworkUpDetector(id:7f521a0d6860))
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |start feeding(NetworkUpDetector(id:7f521a0d6860))
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |feed subscribing for data NetworkUpDetector(id:7f521a0d6860, using ObservableConnection(id:7f521a0e2780)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2978>>])
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |feeding(NetworkUpDetector(id:7f521a0d6860)) started
15:28:29 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-4 |go foreground: NetworkUpDetector(id:7f521a0d6860, using ObservableConnection(id:7f521a0e2780)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2978>>]) - await max. None [sec]
15:28:30 |moler.net_2                                   |     Thread-7 |ping: sendmsg: Network is unreachable

15:28:30 |moler.net_1                                   |     Thread-9 |ping: sendmsg: Network is unreachable

15:28:31 |moler.net_2                                   |     Thread-7 |ping: sendmsg: Network is unreachable

15:28:31 |moler.net_1                                   |     Thread-9 |ping: sendmsg: Network is unreachable

15:28:32 |moler.net_1                                   |     Thread-9 |64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms

15:28:32 |moler.NetworkUpDetector(id:7f521a0e2ba8)      |     Thread-9 |Network 10.0.2.15 is up!
15:28:32 |moler.net_2                                   |     Thread-7 |64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms

15:28:32 |moler.NetworkUpDetector(id:7f521a0d6860)      |     Thread-7 |Network 10.0.2.16 is up!
15:28:32 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |feed done & unsubscribing NetworkUpDetector(id:7f521a0e2ba8, using ObservableConnection(id:7f521a0e2470)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2630>>])
15:28:32 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |END   OF feed(NetworkUpDetector(id:7f521a0e2ba8))
15:28:32 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |feed returning result: 1541514512.3170855
15:28:32 |moler.NetworkUpDetector(id:7f521a0e2ba8)      |     Thread-5 |Observer 'network_toggle_observers.NetworkUpDetector' finished.
15:28:32 |moler.net_1                                   |     Thread-5 |Observer 'network_toggle_observers.NetworkUpDetector' finished.
15:28:32 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |feed done & unsubscribing NetworkUpDetector(id:7f521a0d6860, using ObservableConnection(id:7f521a0e2780)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x7f521a0e2978>>])
15:28:32 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |END   OF feed(NetworkUpDetector(id:7f521a0d6860))
15:28:32 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |feed returning result: 1541514512.3174996
15:28:32 |moler.NetworkUpDetector(id:7f521a0d6860)      |     Thread-5 |Observer 'network_toggle_observers.NetworkUpDetector' finished.
15:28:32 |moler.net_2                                   |     Thread-5 |Observer 'network_toggle_observers.NetworkUpDetector' finished.
15:28:32 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-3 |NetworkUpDetector(id:7f521a0e2ba8) returned 1541514512.3170855
15:28:32 |moler.user.app-code                           |     Thread-3 |Network 10.0.2.15 is back "up" from 15:28:32
15:28:32 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-4 |NetworkUpDetector(id:7f521a0d6860) returned 1541514512.3174996
15:28:32 |moler.user.app-code                           |     Thread-4 |Network 10.0.2.16 is back "up" from 15:28:32
15:28:32 |moler.user.app-code                           |     Thread-3 |exiting ping_observing_task(10.0.2.15)
15:28:32 |moler.user.app-code                           |     Thread-4 |exiting ping_observing_task(10.0.2.16)
15:28:32 |asyncio.main                                  |   MainThread |all jobs observing connections are done
15:28:32 |threaded.ping.tcp-server(5671)                |     Thread-1 |Ping Sim: ... bye
15:28:32 |threaded.ping.tcp-server(5672)                |     Thread-2 |Ping Sim: ... bye
15:28:32 |asyncio                                       |     Thread-5 |poll took 255.669 ms: 1 events
15:28:32 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |... await stop_event done
15:28:32 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Thread-5 |... asyncio-in-thrd loop done
15:28:34 |threaded.ping.tcp-server(5672 -> 43373)       |     Thread-6 |Connection closed
15:28:34 |threaded.ping.tcp-server(5671 -> 49571)       |     Thread-8 |Connection closed
15:28:34 |moler.runner.asyncio-in-thrd:7f521a0d6860     |     Dummy-10 |shutting down
15:28:34 |asyncio                                       |     Dummy-10 |Close <_UnixSelectorEventLoop running=False closed=False debug=True>
'''
