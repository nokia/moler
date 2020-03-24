# -*- coding: utf-8 -*-
"""
External-IO connections based on asyncio.

The only 3 requirements for these connections are:
(1) store Moler's connection inside self.moler_connection attribute
(2) plugin into Moler's connection the way IO outputs data to external world:

    self.moler_connection.how2send = self.send

(3) forward IO received data into self.moler_connection.data_received(data)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import asyncio

from moler.asyncio_runner import get_asyncio_loop_thread
from moler.io.io_connection import IOConnection
import datetime


class AsyncioTcp(IOConnection):
    """Implementation of TCP connection using asyncio."""
    def __init__(self, moler_connection, port, host="localhost", receive_buffer_size=64 * 4096, logger=None):
        """Initialization of TCP connection."""
        super(AsyncioTcp, self).__init__(moler_connection=moler_connection)
        self.moler_connection.how2send = self._send  # need to map synchronous methods
        # TODO: do we want connection.name?
        self.name = moler_connection.name

        self.host = host
        self.port = port
        self.receive_buffer_size = receive_buffer_size
        self.logger = logger  # TODO: build default logger if given is None?
        self._stream_reader = None
        self._stream_writer = None
        self.connection_lost = None

    async def forward_connection_read_data(self):
        while True:
            data = await self._stream_reader.read(self.receive_buffer_size)  # if size not provided it reads till EOF (may block)
            if not data:
                break
            self._debug('< {}'.format(data))
            # forward data to moler-connection
            self.data_received(data, datetime.datetime.now())
        self.connection_lost.set_result(True)  # makes Future done

    async def open(self):
        """Open TCP connection."""
        self._debug('connecting to {}'.format(self))
        # If a task is canceled while it is waiting for another concurrent operation,
        # the task is notified of its cancellation by having a CancelledError exception
        # raised at the point where it is waiting
        try:
            self._stream_reader, self._stream_writer = await asyncio.open_connection(host=self.host, port=self.port)
            # self._stream_reader, self._stream_writer = await asyncio.wait_for(asyncio.open_connection(host=self.host, port=self.port), timeout=10)
        except asyncio.CancelledError as err:
            self._debug("CancelledError while awaiting for open_connection({}), err: {}".format(self, err))
            # TODO: stop child task of asyncio.open_connection
            raise
        else:
            self.connection_lost = asyncio.Future()  # delayed to be created in same loop as open()
            asyncio.ensure_future(self.forward_connection_read_data())
        self._debug('connection {} is open'.format(self))

    async def close(self):
        """
        Close TCP connection.

        Connection should allow for calling close on closed/not-open connection.
        """
        if self._stream_writer:
            self._debug('closing {}'.format(self))
            self._stream_writer.close()
            if self.connection_lost:
                await self.connection_lost
            self._stream_reader = None
            self._stream_writer = None
            self.connection_lost = None
        self._debug('connection {} is closed'.format(self))

    async def __aenter__(self):
        if self._stream_reader is None:
            await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        return False  # reraise exceptions if any

    def _send(self, data):
        self._debug('> {}'.format(data))
        self._stream_writer.write(data)  # TODO: check if we have writer (if open)

    async def send(self, data):
        """
        Send data via TCP service.

        :param data: data
        :type data: str
        """
        self._send(data)
        await self._stream_writer.drain()

    def __str__(self):
        address = 'tcp://{}:{}'.format(self.host, self.port)
        return address

    def _debug(self, msg):  # TODO: refactor to class decorator or so
        if self.logger:
            self.logger.debug(msg)


class AsyncioInThreadTcp(IOConnection):
    """Implementation of TCP connection using asyncio running in dedicated thread."""

    def __init__(self, moler_connection, port, host="localhost", receive_buffer_size=64 * 4096, logger=None):
        """Initialization of TCP connection."""
        super(AsyncioInThreadTcp, self).__init__(moler_connection=moler_connection)
        self.name = moler_connection.name
        # self.moler_connection.how2send = self._send  # need to map synchronous methods
        # TODO: do we want connection.name?
        # self.logger = logger  # TODO: build default logger if given is None?
        self._async_tcp = AsyncioTcp(moler_connection=moler_connection, port=port, host=host,
                                     receive_buffer_size=receive_buffer_size, logger=self.logger)

    def open(self):
        """Open TCP connection."""
        ret = super(AsyncioInThreadTcp, self).open()
        thread4async = get_asyncio_loop_thread()
        thread4async.run_async_coroutine(self._async_tcp.open(), timeout=0.5)
        return ret

    def close(self):
        """
        Close TCP connection.

        Connection should allow for calling close on closed/not-open connection.
        """
        if self._async_tcp._stream_writer:  # change it to coro is_open() checked inside async-thread
            # self._debug('closing {}'.format(self))
            thread4async = get_asyncio_loop_thread()
            ret = thread4async.run_async_coroutine(self._async_tcp.close(), timeout=0.5)
        # self._debug('connection {} is closed'.format(self))
