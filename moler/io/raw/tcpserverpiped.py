# -*- coding: utf-8 -*-
"""
TCP server based on raw sockets and multiprocessing
with services usable for integration tests.

It has backdoor connection over pipe that forms control-service which can:
- inject data that should be server's response for client's request
- send asynchronous data towards client (without awaiting client's request)
- close client connection
- return history of server activity (client connected, data received, ...)
- shutdown server

"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import logging
import select
import socket
import sys
import time
from contextlib import contextmanager
from multiprocessing import Pipe
from multiprocessing import Process
from socket import error as socket_error


@contextmanager
def tcp_server_piped(port=19543, use_stderr_logger=False):
    """
    TCP server context-manager used for integration tests.

    It starts server on localhost/given-port during context-manager start()
    and performs server-cleanup during context-manager stop()

    :param port: where to start server at
    :param use_stderr_logger: configure logging to output into stderr?
    :return: pair (server, inter-process-pipe used to control server)
    """
    client_process_pipe_endpoint, server_pipe_endpoint = Pipe()
    tcp_server = TcpServerPiped(host='localhost', port=port,
                                pipe_in=server_pipe_endpoint, delay=0,
                                use_stderr_logger=use_stderr_logger)
    tcp_server.start()
    time.sleep(0.5)  # allow server to boot-up
    # returning tcp_server let's you call tcp_server.terminate() to kill server
    # for testing dropped TCP connection
    yield (tcp_server, client_process_pipe_endpoint)
    client_process_pipe_endpoint.send(("shutdown", {}))
    tcp_server.join()

# ------------------- TCP server running in separate process ---------------------


class TcpServerPiped(Process):
    def __init__(self, host, port, pipe_in, buffer_size=1024, delay=0,
                 use_stderr_logger=False):
        """Create instance of TcpServerPiped"""
        super(TcpServerPiped, self).__init__()
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.pipe_in = pipe_in
        self.delay = delay
        self.responses = {}
        self.history = []
        self.client_sock = None
        self.server_sock = None
        self.server_is_running = False
        self.use_stderr_logger = use_stderr_logger
        self.logger = None

    def prepare_server_socket(self):
        """Create, configure and start server-listening socket"""
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        svr_addr = (self.host, self.port)
        self.server_sock.bind(svr_addr)
        self.server_sock.setblocking(True)
        self.server_sock.listen(1)
        self.logger.debug(f"listening on {svr_addr[0]}:{svr_addr[1]}")

    def handle_controlling_action(self):
        """Handle actions coming from server-controlling pipe"""
        input_msg = None
        try:
            if self.pipe_in.poll(0.01):
                input_msg = self.pipe_in.recv()
        except IOError:
            if self.client_sock is not None:
                self.logger.debug(f"closing cli sock {self.client_sock} (on pipe's IOError)")
                self.client_sock.close()
                self.client_sock = None
            self.server_is_running = False
        else:
            if input_msg:
                self.interpret_pipe_msg(input_msg)

    def check_and_handle_server_socket(self):
        """Check if client is knocking :-)"""
        ready = select.select([self.server_sock], [], [], 0.001)
        if ready[0]:
            self.handle_incomming_client()

    def check_and_handle_client_socket(self):
        """Handle data coming from client connection"""
        ready = select.select([self.client_sock], [], [], 0.001)
        if ready[0]:
            try:
                data = self.client_sock.recv(self.buffer_size)
                if not data:
                    self.handle_leaving_client()
                else:
                    self.handle_data(data)
            except socket_error as serr:
                if (serr.errno == 10054) or (serr.errno == 10053) or (serr.errno == 10061):
                    self.server_is_running = False  # endpoint disconnected

    def handle_incomming_client(self):
        """Accept incoming client - make socket connection for it"""
        self.client_sock, addr = self.server_sock.accept()
        self.logger.debug(f"accepted cli sock {self.client_sock}")
        self.history.append('Client connected')
        self.history.append(f'Client details: {addr}')

    def handle_leaving_client(self):
        """Handle client leaving server"""
        self.history.append('Client disconnected')
        if self.client_sock is not None:
            self.logger.debug(f"closing cli sock {self.client_sock} (on leaving)")
            self.client_sock.close()
            self.client_sock = None

    def handle_data(self, data):
        """Handle data that came from client"""
        self.history.append(['Received data:', data])
        if data in self.responses:
            response = self.responses[data]
            self.history.append(['Sending response:', data])
            self.client_sock.send(response)
            del self.responses[data]

    def interpret_pipe_msg(self, msg):
        """Interpret message that came from controlling pipe"""
        (action, data) = msg
        try:
            func = getattr(self, f"do_{action.replace(' ', '_')}")
        except AttributeError:
            self.history.append(f'Unknown action: "{str(action)}"')
        else:
            return func(**data)

    def do_shutdown(self, **kwargs):
        """
        Handles following pipe message
        ("shutdown", {})
        Force server to shut down
        """
        self.do_close_connection(**kwargs)
        self.server_is_running = False

    # pylint: disable-next=unused-argument
    def do_close_connection(self, **kwargs):
        """
        Handles following pipe message
        ("close connection", {})
        Force server to close connection to client
        """
        if self.client_sock is not None:
            self.history.append('Closing client connection')
            self.logger.debug(f'Closing client connection {self.client_sock} (on do_close request)')
            self.client_sock.close()
            self.client_sock = None

    def do_set_delay(self, **kwargs):
        """
        Handles following pipe message
        ("set delay", {'delay': 2.5})
        It defines how much we should delay sending response
        """
        if 'delay' in kwargs:
            self.delay = kwargs['delay']
        else:
            err = f'data for "set delay" must contain "delay" key - not {kwargs}'
            self.history.append(err)

    def do_inject_response(self, **kwargs):
        """
        Handles following pipe message
        ("inject response", {'req': rpc_startup_msg, 'resp': response_for_rpc_startup_msg})
        It defines response ('resp') that should be send by server
        in reaction to received client data ('req').
        """
        if ('req' in kwargs) and ('resp' in kwargs):
            request = kwargs['req']
            response = kwargs['resp']
            self.responses[request] = response
        else:
            err = f'data for "inject response" must contain "req" and "resp" keys - not {kwargs}'
            self.history.append(err)

    # pylint: disable-next=unused-argument
    def do_get_history(self, **kwargs):
        """
        Handles following pipe message
        ("get history", {})
        Retrieve server's history
        """
        self.pipe_in.send(self.history)

    def do_send_async_msg(self, **kwargs):
        """
        Handles following pipe message
        ("send async msg", {'msg': msg_payload})
        It injects message to be send by server 'just now'
        (without awaiting any data from client)
        """
        if 'msg' in kwargs:
            async_msg = kwargs['msg']
            log_msg = f'Sending asynchronous msg: {str(async_msg)}'
            self.history.append(['Sending asynchronous msg:', async_msg])
            self.logger.debug(f"{log_msg} to cli sock {self.client_sock}")
            self.client_sock.send(async_msg)
        else:
            err = f'data for "send async msg" must contain "msg" key - not {kwargs}'
            self.history.append(err)

    def configure_stderr_logger(self):
        """Configure logging output on stderr"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s |%(name)-40s |%(message)s',
            datefmt='%H:%M:%S',
            stream=sys.stderr,
        )

    def run(self):
        """Run main loop of server process"""
        if self.use_stderr_logger:
            self.configure_stderr_logger()
        self.logger = logging.getLogger('moler.io.raw.tcp-svr-piped')
        self.logger.debug("starting process of TcpServerPiped")
        self.prepare_server_socket()
        self.history = []
        self.server_is_running = True
        try:
            self.logger.debug("TcpServerPiped running")
            while self.server_is_running:
                self.handle_controlling_action()
                if self.client_sock is None:  # no client connected yet
                    self.check_and_handle_server_socket()
                else:
                    self.check_and_handle_client_socket()
        except Exception as err:
            err_msg = f"TcpServerPiped error: {err} - history: {self.history}"
            self.logger.debug(err_msg)
        self.logger.debug("TcpServerPiped process is gone")
