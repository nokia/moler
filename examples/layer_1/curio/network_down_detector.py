# -*- coding: utf-8 -*-
# Copyright (C) 2018 Nokia
"""
curio.network_down_detector.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A fully-functional connection-observer using curio. Requires Python 3.6+.

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
import curio
import logging
import sys
import time

from moler.connection_observer import ConnectionObserver
from moler.connection import ObservableConnection

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


async def ping_sim_tcp_server(client, address):
    logger = logging.getLogger('curio.ping.tcp-server')
    logger.debug('connection accepted - client at tcp://{}:{}'.format(*address))

    ping_lines = ping_output.splitlines(keepends=True)
    async with client:
        for ping_line in ping_lines:
            data = ping_line.encode(encoding='utf-8')
            await client.sendall(data)
            await curio.sleep(1)  # simulate delay between ping lines
    logger.info('Connection closed')


async def start_ping_sim_server(server_address):
    """Run server simulating ping command output, this is one-shot server"""
    logger = logging.getLogger('curio.ping.tcp-server')
    host, port = server_address
    try:
        async with curio.TaskGroup() as g:
            await g.spawn(curio.tcp_server, host, port, ping_sim_tcp_server)
            info = "Ping Sim started at tcp://{}:{}".format(*server_address)
            logger.debug(info)
            info = "WARNING - I'll be tired too much just after first client!"
            logger.debug(info)
    except curio.CancelledError:
        logger.debug("Ping Sim: You are right - I'm tired after this client")


async def tcp_connection(address):
    """Async generator reading from tcp network transport layer"""
    logger = logging.getLogger('curio.tcp-connection')
    logger.debug('... connecting to tcp://{}:{}'.format(*address))
    host, port = address
    sock = await curio.open_connection(host, port)
    async with sock:
        while True:
            data = await sock.recv(128)
            if data:
                logger.debug('<<< {!r}'.format(data))
                yield data
            else:
                break


async def main(host, port):
    logger = logging.getLogger('curio.main')
    # Starting the server
    serv_task = await curio.spawn(start_ping_sim_server, (host, port))
    # Starting the client
    cli_task = await curio.spawn(ping_observing_task, (host, port))
    await cli_task.join()
    # Client is done
    # One-shot server - so we shutting it down
    await serv_task.cancel()

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
    async with curio.meta.finalize(tcp_connection(address)) as tcp_conn:
        async for connection_data in tcp_conn:
            # 3b. glue to proxy from external-IO (asyncio tcp client connection)
            #    (client has to pass it's received data into Moler's connection)
            moler_conn.data_received(connection_data)
            # 4. Moler's client code must manually check status of observer ...
            if net_down_detector.done():
                # 5. ... to know when it can ask for result
                net_down_time = net_down_detector.result()
                timestamp = time.strftime("%H:%M:%S",
                                          time.localtime(net_down_time))
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
    # --------------------------------------------------------------------
    import platform
    if platform.system() == 'Windows':
        # need workaround:   https://github.com/dabeaz/curio/issues/75
        import selectors
        import socket as stdlib_socket
        dummy_socket = stdlib_socket.socket(stdlib_socket.AF_INET,
                                            stdlib_socket.SOCK_DGRAM)
        selector = selectors.DefaultSelector()
        selector.register(dummy_socket, selectors.EVENT_READ)
    # --------------------------------------------------------------------
    curio.run(main, '', 5679, selector=selector)
