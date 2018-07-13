# -*- coding: utf-8 -*-
"""
asyncio.network_down_detector.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A fully-functional connection-observer using asyncio. Requires Python 3.6+.

This example demonstrates basic concept of connection observer - entity
that is fully responsible for:
- observing data coming from connection till it catches what it is waiting for
- parsing that data to have "caught event" stored in expected form
- storing that result internally for later retrieval

Please note that this example is LAYER-1 usage which means:
- observer can't run by its own, must be fed with data (passive observer)
- observer can't be awaited, must be queried for status before asking for data
Another words - low level manual combining of all the pieces.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import asyncio
import functools
import logging
import sys
import time

from moler.connection import ObservableConnection
from moler.connection_observer import ConnectionObserver

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


async def ping_sim_tcp_server(client_handling_done, reader, writer):
    """Replay ping command output toward connected client"""
    logger = logging.getLogger('asyncio.ping.tcp-server')
    address = writer.get_extra_info('peername')
    logger.debug('connection accepted - client at tcp://{}:{}'.format(*address))

    ping_lines = ping_output.splitlines(keepends=True)
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


def start_ping_sim_server(server_address):
    """Run server simulating ping command output, this is one-shot server"""
    logger = logging.getLogger('asyncio.ping.tcp-server')
    client_handling_done = asyncio.Future()
    handle_client = functools.partial(ping_sim_tcp_server, client_handling_done)
    factory = asyncio.start_server(handle_client, *server_address)
    server = asyncio.get_event_loop().run_until_complete(factory)
    logger.debug("Ping Sim started at tcp://{}:{}".format(*server_address))

    def shutdown_server(client_done_future):
        logger.debug("Ping Sim: I'm tired after this client ... will do sepuku")
        server.close()
    client_handling_done.add_done_callback(shutdown_server)
    logger.debug("WARNING - I'll be tired too much just after first client!")
    return server


async def tcp_connection(address):
    """Async generator reading from tcp network transport layer"""
    logger = logging.getLogger('asyncio.tcp-connection')
    logger.debug('... connecting to tcp://{}:{}'.format(*address))
    reader, writer = await asyncio.open_connection(*address)
    try:
        while True:
            data = await reader.read(128)
            if data:
                logger.debug('<<< {!r}'.format(data))
                yield data
            else:
                break
    finally:
        logger.debug('... closing')
        writer.close()


# ===================== Moler's connection-observer usage ======================
class NetworkDownDetector(ConnectionObserver):
    def __init__(self):
        super(NetworkDownDetector, self).__init__()
        self.logger = logging.getLogger('moler.net-down-detector')

    def data_received(self, data):
        if not self.done():
            if "Network is unreachable" in data:  # observer operates on strings
                when_network_down_detected = time.time()
                self.logger.debug("Network is down!")
                self.set_result(result=when_network_down_detected)


async def ping_observing_task(address):
    logger = logging.getLogger('moler.user.app-code')

    # Lowest layer of Moler's usage (you manually glue all elements):
    # 1. create observer
    net_down_detector = NetworkDownDetector()
    # 2. ObservableConnection is a proxy-glue between observer (speaks str)
    #                                   and asyncio-connection (speaks bytes)
    moler_conn = ObservableConnection(decoder=lambda data: data.decode("utf-8"))
    # 3a. glue from proxy to observer
    moler_conn.subscribe(net_down_detector.data_received)

    logger.debug('waiting for data to observe')
    async for connection_data in tcp_connection(address):
        # 3b. glue to proxy from external-IO (asyncio tcp client connection)
        #   (client code has to pass it's received data into Moler's connection)
        moler_conn.data_received(connection_data)
        # 4. Moler's client code must manually check status of observer ...
        if net_down_detector.done():
            # 5. ... to know when it can ask for result
            net_down_time = net_down_detector.result()
            timestamp = time.strftime("%H:%M:%S", time.localtime(net_down_time))
            logger.debug('Network is down from {}'.format(timestamp))
            break


# ==============================================================================
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s |%(name)25s |%(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )
    event_loop = asyncio.get_event_loop()
    server_address = ('127.0.0.1', 5678)
    server = start_ping_sim_server(server_address)
    try:
        event_loop.run_until_complete(ping_observing_task(server_address))
    finally:
        event_loop.run_until_complete(server.wait_closed())
        event_loop.close()

'''
LOG OUTPUT

16:56:30 |                  asyncio |Using selector: SelectSelector
16:56:30 |  asyncio.ping.tcp-server |Ping Sim started at tcp://127.0.0.1:5678
16:56:30 |  asyncio.ping.tcp-server |WARNING - I'll be tired too much just after first client!
16:56:30 |      moler.user.app-code |waiting for data to observe
16:56:30 |   asyncio.tcp-connection |... connecting to tcp://127.0.0.1:5678
16:56:30 |  asyncio.ping.tcp-server |connection accepted - client at tcp://127.0.0.1:56556
16:56:30 |   asyncio.tcp-connection |<<< b'\n'
16:56:31 |   asyncio.tcp-connection |<<< b'greg@debian:~$ ping 10.0.2.15\n'
16:56:32 |   asyncio.tcp-connection |<<< b'PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.\n'
16:56:33 |   asyncio.tcp-connection |<<< b'64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms\n'
16:56:34 |   asyncio.tcp-connection |<<< b'64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms\n'
16:56:35 |   asyncio.tcp-connection |<<< b'64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms\n'
16:56:36 |   asyncio.tcp-connection |<<< b'ping: sendmsg: Network is unreachable\n'
16:56:36 |  moler.net-down-detector |Network is down!
16:56:36 |      moler.user.app-code |Network is down from 16:56:36
16:56:36 |   asyncio.tcp-connection |... closing
16:56:38 |  asyncio.ping.tcp-server |Ping Sim: I'm tired after this client ... will do sepuku
'''
