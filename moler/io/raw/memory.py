# -*- coding: utf-8 -*-
"""
External-IO connections based on memory buffer.

The only 3 requirements for these connections are:
(1) store Moler's connection inside self.moler_connection attribute
(2) plugin into Moler's connection the way IO outputs data to external world:
    self.moler_connection.how2send = self.send
(3) forward IO received data into self.moler_connection.data_received(data)
"""
import threading
import time

from moler.io.io_connection import IOConnection
from moler.io.raw import TillDoneThread

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


class FifoBuffer(IOConnection):
    r"""
    FIFO-in-memory.::

        inject             |\
                 +---------+ \  read
        write    +---------+ /
                           |/

    Usable for unit tests (manually inject what is expected).
    """
    def __init__(self, moler_connection, echo=True, logger=None):
        """Initialization of FIFO-in-memory connection."""
        super(FifoBuffer, self).__init__(moler_connection=moler_connection)
        # TODO: do we want connection.name?
        self.echo = echo
        self.logger = logger  # TODO: build default logger if given is None?
        self.buffer = bytearray()

    def inject(self, input_bytes):
        """Add bytes to end of buffer"""
        self.buffer.extend(input_bytes)

    def write(self, input_bytes):
        """
        What is written to connection comes back on read()
        only if we simulate echo service of remote end.
        """
        if self.echo:
            self.inject(input_bytes)

    send = write  # just alias to make base class happy :-)

    def read(self, bufsize=None):
        """Remove bytes from front of buffer"""
        if bufsize is None:
            size2read = len(self.buffer)
        elif len(self.buffer) >= bufsize:
            size2read = bufsize
        else:
            size2read = len(self.buffer)
        if size2read > 0:
            data = self.buffer[:size2read]
            self.buffer = self.buffer[size2read:]
            self.data_received(data)
            return data
        else:
            return b''

    receive = read  # just alias to make base class happy :-)

    def __str__(self):
        address = 'tcp://{}:{}'.format(self.host, self.port)
        return address

    def _debug(self, msg):  # TODO: refactor to class decorator or so
        if self.logger:
            self.logger.debug(msg)


class ThreadedFifoBuffer(FifoBuffer):
    """
    FIFO-in-memory connection inside dedicated thread.

    This is external-IO usable for Moler since it has it's own runner
    (thread) that can work in background and pull data from FIFO-mem connection.
    Usable for integration tests.
    """

    def __init__(self, moler_connection, echo=True, logger=None):
        """Initialization of FIFO-mem-threaded connection."""
        super(ThreadedFifoBuffer, self).__init__(moler_connection=moler_connection,
                                                 echo=echo,
                                                 logger=logger)
        self.pulling_thread = None

    def open(self):
        """Start thread pulling data from FIFO buffer."""
        super(ThreadedFifoBuffer, self).open()
        done = threading.Event()
        self.pulling_thread = TillDoneThread(target=self.pull_data,
                                             done_event=done,
                                             kwargs={'pulling_done': done})
        self.pulling_thread.start()

    def close(self):
        """Stop pulling thread."""
        if self.pulling_thread:
            self.pulling_thread.join()
            self.pulling_thread = None
        super(ThreadedFifoBuffer, self).close()

    def pull_data(self, pulling_done):
        """Pull data from FIFO buffer."""
        while not pulling_done.is_set():
            self.read()  # internally forwards to embedded Moler connection
            time.sleep(0.1)  # give FIFO chance to get data
