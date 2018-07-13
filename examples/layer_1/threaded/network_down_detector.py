# -*- coding: utf-8 -*-
"""
threaded.network_down_detector.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A fully-functional connection-observer using socket & threading.
Works on Python 2.7 as well as on 3.6

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
import logging
import select
import socket
import sys
import threading
import time
from contextlib import closing

from moler.connection import ObservableConnection
from moler.connection_observer import ConnectionObserver

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

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


def ping_sim_tcp_server(client, address):
    logger = logging.getLogger('threaded.ping.tcp-server')
    logger.debug('connection accepted - client at tcp://{}:{}'.format(*address))

    ping_lines = ping_output.splitlines(True)
    with closing(client):
        for ping_line in ping_lines:
            data = ping_line.encode(encoding='utf-8')
            try:
                client.sendall(data)
            except socket.error:  # client is gone
                break
            time.sleep(1)  # simulate delay between ping lines
    logger.info('Connection closed')


def server_loop(server_socket, done_event):
    logger = logging.getLogger('threaded.ping.tcp-server')
    while not done_event.is_set():
        # without select we can't break loop from outside (via done_event)
        # since .accept() is blocking
        read_sockets, _, _ = select.select([server_socket], [], [], 0.1)
        if not read_sockets:
            continue
        client_socket, client_addr = server_socket.accept()
        client_socket.setblocking(1)
        client_thread = threading.Thread(target=ping_sim_tcp_server,
                                         args=(client_socket, client_addr))
        client_thread.start()
    logger.debug("Ping Sim: I'm tired after this client ... bye")


def start_ping_sim_server(server_address):
    """Run server simulating ping command output, this is one-shot server"""
    logger = logging.getLogger('threaded.ping.tcp-server')
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(server_address)
    server_socket.listen(1)
    logger.debug("Ping Sim started at tcp://{}:{}".format(*server_address))
    logger.debug("WARNING - I'll be tired too much just after first client!")
    done_event = threading.Event()
    server_thread = threading.Thread(target=server_loop,
                                     args=(server_socket, done_event))
    server_thread.start()
    return server_thread, done_event


def tcp_connection(address):
    """Generator reading from tcp network transport layer"""
    logger = logging.getLogger('threaded.tcp-connection')
    logger.debug('... connecting to tcp://{}:{}'.format(*address))
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(address)

    with closing(client_socket):
        while True:
            data = client_socket.recv(128)
            if data:
                logger.debug('<<< {!r}'.format(data))
                yield data
            else:
                logger.debug("... closed")
                break


def main(address):
    # Starting the server - in threads: sever loop, handling accepted clients
    server_thread, server_done = start_ping_sim_server(address)
    # Starting the client
    client_thread = threading.Thread(target=ping_observing_task, args=(address,))
    client_thread.start()  # client connection also works in thread
    client_thread.join()
    server_done.set()
    server_thread.join()


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


def ping_observing_task(address):
    logger = logging.getLogger('moler.user.app-code')

    # Lowest layer of Moler's usage (you manually glue all elements):
    # 1. create observer
    net_down_detector = NetworkDownDetector()
    # 2. ObservableConnection is a proxy-glue between observer (speaks str)
    #                                   and threaded-connection (speaks bytes)
    moler_conn = ObservableConnection(decoder=lambda data: data.decode("utf-8"))
    # 3a. glue from proxy to observer
    moler_conn.subscribe(net_down_detector.data_received)

    logger.debug('waiting for data to observe')
    for connection_data in tcp_connection(address):
        # 3b. glue to proxy from external-IO (threaded tcp client connection)
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
    local_address = ('localhost', 5670)
    main(local_address)

'''
LOG OUTPUT

16:58:04 | threaded.ping.tcp-server |Ping Sim started at tcp://localhost:5670
16:58:04 | threaded.ping.tcp-server |WARNING - I'll be tired too much just after first client!
16:58:04 |      moler.user.app-code |waiting for data to observe
16:58:04 |  threaded.tcp-connection |... connecting to tcp://localhost:5670
16:58:04 | threaded.ping.tcp-server |connection accepted - client at tcp://127.0.0.1:56582
16:58:04 |  threaded.tcp-connection |<<< b'\n'
16:58:05 |  threaded.tcp-connection |<<< b'greg@debian:~$ ping 10.0.2.15\n'
16:58:06 |  threaded.tcp-connection |<<< b'PING 10.0.2.15 (10.0.2.15) 56(84) bytes of data.\n'
16:58:07 |  threaded.tcp-connection |<<< b'64 bytes from 10.0.2.15: icmp_req=1 ttl=64 time=0.080 ms\n'
16:58:08 |  threaded.tcp-connection |<<< b'64 bytes from 10.0.2.15: icmp_req=2 ttl=64 time=0.037 ms\n'
16:58:09 |  threaded.tcp-connection |<<< b'64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms\n'
16:58:10 |  threaded.tcp-connection |<<< b'ping: sendmsg: Network is unreachable\n'
16:58:10 |  moler.net-down-detector |Network is down!
16:58:10 |      moler.user.app-code |Network is down from 16:58:10
16:58:10 | threaded.ping.tcp-server |Ping Sim: I'm tired after this client ... bye
16:58:12 | threaded.ping.tcp-server |Connection closed
'''
