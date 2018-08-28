# -*- coding: utf-8 -*-
"""
asyncio_runner_with_only_async_functions.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
import functools
import time
import asyncio

from moler.connection import ObservableConnection
from moler.connection_observer import ConnectionObserver
from moler.io.raw import tcp
from moler.connection import get_connection, ConnectionFactory
from moler.asyncio_runner import AsyncioRunner

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


async def ping_sim_tcp_server(server_port, ping_ip, client_handling_done, reader, writer):
    address = writer.get_extra_info('peername')
    _, client_port = address
    logger = logging.getLogger('asyncio.ping.tcp-server({} -> {})'.format(server_port,
                                                                          client_port))
    logger.debug('connection accepted - client at tcp://{}:{}'.format(*address))
    ping_out = ping_output.replace("10.0.2.15", ping_ip)
    ping_lines = ping_out.splitlines(True)
    for ping_line in ping_lines:
        data = ping_line.encode(encoding='utf-8')
        writer.write(data)
        try:
            await writer.drain()
        except ConnectionResetError:  # client is gone
            break
        await asyncio.sleep(1)  # simulate delay between ping lines
    writer.close()
    client_handling_done.set_result(True)
    logger.info('Connection tcp://{}:{} closed'.format(*address))


async def start_ping_sim_server(server_address, ping_ip):
    """Run server simulating ping command output, this is one-shot server"""
    _, server_port = server_address
    logger = logging.getLogger('asyncio.ping.tcp-server({})'.format(server_port))
    client_handling_done = asyncio.Future()
    handle_client = functools.partial(ping_sim_tcp_server, server_port,
                                      ping_ip, client_handling_done)
    factory = asyncio.start_server(handle_client, *server_address)
    server = await factory
    logger.debug("Ping Sim started at tcp://{}:{}".format(*server_address))

    def shutdown_server(client_done_future):
        logger.debug("Ping Sim: I'm tired after this client ... will do sepuku")
        server.close()
    client_handling_done.add_done_callback(shutdown_server)
    logger.debug("WARNING - I'll be tired too much just after first client!")
    return server


async def main(connections2observe4ip):
    logger = logging.getLogger('asyncio.main')
    event_loop = asyncio.get_event_loop()
    # Starting the servers
    servers = []
    for address, _, ping_ip in connections2observe4ip:
        # simulate pinging given IP
        server = await start_ping_sim_server(address, ping_ip)
        servers.append(server)
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
        tcp_connection = get_connection(name=connection_name, logger=logger)
        tcp_connection.moler_connection.name = connection_name
        # client_task= asyncio.ensure_future(ping_observing_task(tcp_connection, ping_ip))
        connections.append(ping_observing_task(tcp_connection, ping_ip))
    # await observers job to be done
    completed, pending = await asyncio.wait(connections)

    # stop servers
    for server in servers:
        await server.wait_closed()
    logger.debug('exiting main')


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
        # net_down_time = net_down_detector.await_done(timeout=10)
        # net_down_time = await net_down_detector
        net_down_time = 8
        timestamp = time.strftime("%H:%M:%S", time.localtime(net_down_time))
        logger.debug('Network {} is down from {}'.format(ping_ip, timestamp))

        # 6. call next observer (blocking till completes)
        info = '{} on {} using {}'.format(ping_ip, conn_addr, net_up_detector)
        logger.debug('observe ' + info)
        # using as synchronous function (so we want verb to express action)
        # detect_network_up = net_up_detector
        # net_up_time = detect_network_up()
        # timestamp = time.strftime("%H:%M:%S", time.localtime(net_up_time))
        # logger.debug('Network {} is back "up" from {}'.format(ping_ip, timestamp))
        await asyncio.sleep(2)
    logger.debug('exiting ping_observing_task')


# ==============================================================================
if __name__ == '__main__':
    import os
    from moler.config import load_config
    # -------------------------------------------------------------------
    # Configure moler connections (backend code)
    # 1) configure variant by YAML config file
    # 2) ver.2 - configure named connections by YAML config file
    load_config(path=os.path.join(os.path.dirname(__file__), "..", "named_connections.yml"))

    # 3) take default class used to realize tcp-threaded-connection
    # -------------------------------------------------------------------

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s |%(name)-40s |%(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )
    connections2observe4ip = [(('localhost', 5671), 'net_1', '10.0.2.15'),
                              (('localhost', 5672), 'net_2', '10.0.2.16')]

    asyncio.set_event_loop(asyncio.new_event_loop())
    event_loop = asyncio.get_event_loop()
    event_loop.set_debug(enabled=True)
    try:
        event_loop.run_until_complete(main(connections2observe4ip))
    finally:
        event_loop.close()

'''
LOG OUTPUT

20:22:28 |asyncio                                  |Using selector: SelectSelector
20:22:28 |threaded.ping.tcp-server(5671)           |Ping Sim started at tcp://localhost:5671
20:22:28 |asyncio                                  |Using selector: SelectSelector
20:22:28 |threaded.ping.tcp-server(5672)           |Ping Sim started at tcp://localhost:5672
20:22:28 |asyncio                                  |Using selector: SelectSelector
20:22:28 |moler.runner.asyncio                     |created
20:22:28 |moler.runner.asyncio                     |created
20:22:28 |moler.user.app-code                      |observe 10.0.2.16 on tcp://localhost:5672 using NetworkDownDetector(id:3096518)
20:22:28 |moler.runner.asyncio                     |go background: NetworkDownDetector(id:3096518, using ObservableConnection(id:30964e0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096588>>])
20:22:28 |moler.runner.asyncio                     |subscribing for data NetworkDownDetector(id:3096518, using ObservableConnection(id:30964e0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096588>>])
20:22:28 |moler.runner.asyncio                     |go foreground: NetworkDownDetector(id:3096518, using ObservableConnection(id:30964e0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096588>>]) - await max. 10 [sec]
20:22:28 |moler.runner.asyncio                     |created
20:22:28 |moler.runner.asyncio                     |created
20:22:28 |moler.user.app-code                      |observe 10.0.2.15 on tcp://localhost:5671 using NetworkDownDetector(id:3096b70)
20:22:28 |asyncio                                  |Using selector: SelectSelector
20:22:28 |moler.runner.asyncio                     |go background: NetworkDownDetector(id:3096b70, using ObservableConnection(id:30961d0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096278>>])
20:22:28 |moler.runner.asyncio                     |subscribing for data NetworkDownDetector(id:3096b70, using ObservableConnection(id:30961d0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096278>>])
20:22:28 |threaded.ping.tcp-server(5672 -> 51747)  |connection accepted - client at tcp://127.0.0.1:51747
20:22:28 |moler.connection.net_2                   |b'\n'
20:22:28 |moler.runner.asyncio                     |go foreground: NetworkDownDetector(id:3096b70, using ObservableConnection(id:30961d0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096278>>]) - await max. 10 [sec]
20:22:28 |asyncio                                  |Using selector: SelectSelector
20:22:28 |moler.runner.asyncio                     |START OF feed(NetworkDownDetector(id:3096518))
20:22:28 |moler.runner.asyncio                     |START OF feed(NetworkDownDetector(id:3096b70))
20:22:28 |threaded.ping.tcp-server(5671 -> 51752)  |connection accepted - client at tcp://127.0.0.1:51752
20:22:28 |moler.connection.net_1                   |b'\n'
20:22:29 |moler.connection.net_2                   |b'greg@debian:~$ ping 10.0.2.16\n'
20:22:29 |moler.connection.net_1                   |b'greg@debian:~$ ping 10.0.2.15\n'
20:22:30 |moler.connection.net_2                   |b'PING 10.0.2.16 (10.0.2.16) 56(84) bytes of data.\n'
20:22:30 |moler.connection.net_1                   |b'PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.\n'
20:22:31 |moler.connection.net_2                   |b'64 bytes from 10.0.2.16: icmp_req=1 ttl=64 time=0.080 ms\n'
20:22:31 |moler.connection.net_1                   |b'64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms\n'
20:22:32 |moler.connection.net_2                   |b'64 bytes from 10.0.2.16: icmp_req=2 ttl=64 time=0.037 ms\n'
20:22:32 |moler.connection.net_1                   |b'64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms\n'
20:22:33 |moler.connection.net_2                   |b'64 bytes from 10.0.2.16: icmp_req=3 ttl=64 time=0.045 ms\n'
20:22:33 |moler.connection.net_1                   |b'64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms\n'
20:22:34 |moler.connection.net_2                   |b'ping: sendmsg: Network is unreachable\n'
20:22:34 |moler.NetworkDownDetector(id:3096518)    |Network 10.0.2.16 is down!
20:22:34 |moler.connection.net_1                   |b'ping: sendmsg: Network is unreachable\n'
20:22:34 |moler.NetworkDownDetector(id:3096b70)    |Network 10.0.2.15 is down!
20:22:34 |moler.user.app-code                      |Network 10.0.2.15 is down from 20:22:34
20:22:34 |moler.user.app-code                      |observe 10.0.2.15 on tcp://localhost:5671 using NetworkUpDetector(id:3096a20)
20:22:34 |moler.runner.asyncio                     |go background: NetworkUpDetector(id:3096a20, using ObservableConnection(id:30961d0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096278>>])
20:22:34 |moler.runner.asyncio                     |subscribing for data NetworkUpDetector(id:3096a20, using ObservableConnection(id:30961d0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096278>>])
20:22:34 |moler.runner.asyncio                     |go foreground: NetworkUpDetector(id:3096a20, using ObservableConnection(id:30961d0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096278>>]) - await max. None [sec]
20:22:34 |moler.runner.asyncio                     |done & unsubscribing NetworkDownDetector(id:3096518, using ObservableConnection(id:30964e0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096588>>])
20:22:34 |moler.runner.asyncio                     |returning result NetworkDownDetector(id:3096518)
20:22:34 |moler.runner.asyncio                     |END   OF feed(NetworkDownDetector(id:3096518))
20:22:34 |moler.runner.asyncio                     |done & unsubscribing NetworkDownDetector(id:3096b70, using ObservableConnection(id:30961d0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096278>>])
20:22:34 |moler.runner.asyncio                     |returning result NetworkDownDetector(id:3096b70)
20:22:34 |moler.runner.asyncio                     |END   OF feed(NetworkDownDetector(id:3096b70))
20:22:34 |moler.runner.asyncio                     |START OF feed(NetworkUpDetector(id:3096a20))
20:22:35 |moler.connection.net_2                   |b'ping: sendmsg: Network is unreachable\n'
20:22:35 |moler.connection.net_1                   |b'ping: sendmsg: Network is unreachable\n'
20:22:36 |moler.connection.net_2                   |b'ping: sendmsg: Network is unreachable\n'
20:22:36 |moler.connection.net_1                   |b'ping: sendmsg: Network is unreachable\n'
20:22:37 |moler.connection.net_2                   |b'64 bytes from 10.0.2.16: icmp_req=7 ttl=64 time=0.123 ms\n'
20:22:37 |moler.connection.net_1                   |b'64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms\n'
20:22:37 |moler.NetworkUpDetector(id:3096a20)      |Network 10.0.2.15 is up!
20:22:37 |moler.user.app-code                      |Network 10.0.2.15 is back "up" from 20:22:37
20:22:37 |asyncio                                  |Exception in callback <TaskSendMethWrapper object at 0x0000000003096AC8>()
handle: <Handle <TaskSendMethWrapper object at 0x0000000003096AC8>()>
Traceback (most recent call last):
  File "C:\Python36\lib\asyncio\events.py", line 126, in _run
    self._callback(*self._args)
KeyError: <_WindowsSelectorEventLoop running=True closed=False debug=False>
20:22:37 |moler.runner.asyncio                     |done & unsubscribing NetworkUpDetector(id:3096a20, using ObservableConnection(id:30961d0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096278>>])
20:22:37 |moler.runner.asyncio                     |returning result NetworkUpDetector(id:3096a20)
20:22:37 |moler.runner.asyncio                     |END   OF feed(NetworkUpDetector(id:3096a20))
20:22:37 |moler.user.app-code                      |Network 10.0.2.16 is down from 20:22:34
20:22:37 |moler.user.app-code                      |observe 10.0.2.16 on tcp://localhost:5672 using NetworkUpDetector(id:3096828)
20:22:37 |moler.runner.asyncio                     |go background: NetworkUpDetector(id:3096828, using ObservableConnection(id:30964e0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096588>>])
20:22:37 |moler.runner.asyncio                     |subscribing for data NetworkUpDetector(id:3096828, using ObservableConnection(id:30964e0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096588>>])
20:22:37 |moler.runner.asyncio                     |go foreground: NetworkUpDetector(id:3096828, using ObservableConnection(id:30964e0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096588>>]) - await max. None [sec]
20:22:37 |moler.runner.asyncio                     |START OF feed(NetworkUpDetector(id:3096828))
20:22:38 |moler.connection.net_2                   |b'64 bytes from 10.0.2.16: icmp_req=8 ttl=64 time=0.056 ms\n'
20:22:38 |moler.NetworkUpDetector(id:3096828)      |Network 10.0.2.16 is up!
20:22:38 |moler.user.app-code                      |Network 10.0.2.16 is back "up" from 20:22:38
20:22:38 |asyncio                                  |Exception in callback <TaskSendMethWrapper object at 0x00000000022CD6D8>()
handle: <Handle <TaskSendMethWrapper object at 0x00000000022CD6D8>()>
Traceback (most recent call last):
  File "C:\Python36\lib\asyncio\events.py", line 126, in _run
    self._callback(*self._args)
KeyError: <_WindowsSelectorEventLoop running=True closed=False debug=False>
20:22:38 |moler.runner.asyncio                     |done & unsubscribing NetworkUpDetector(id:3096828, using ObservableConnection(id:30964e0)-->[<bound method Tcp.send of <moler.io.raw.tcp.ThreadedTcp object at 0x0000000003096588>>])
20:22:38 |moler.runner.asyncio                     |returning result NetworkUpDetector(id:3096828)
20:22:38 |moler.runner.asyncio                     |END   OF feed(NetworkUpDetector(id:3096828))
20:22:38 |threaded.ping.tcp-server(5671)           |Ping Sim: ... bye
20:22:38 |threaded.ping.tcp-server(5672)           |Ping Sim: ... bye
20:22:39 |threaded.ping.tcp-server(5672 -> 51747)  |Connection closed
20:22:39 |threaded.ping.tcp-server(5671 -> 51752)  |Connection closed
20:22:39 |moler.runner.asyncio                     |shutting down
20:22:39 |moler.runner.asyncio                     |shutting down
20:22:39 |moler.runner.asyncio                     |shutting down
20:22:39 |moler.runner.asyncio                     |shutting down
'''
