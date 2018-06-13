__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import re
import select
from threading import Event

from ptyprocess import PtyProcessUnicode

from moler.io.io_connection import IOConnection
from moler.io.raw import TillDoneThread


class Terminal(IOConnection):
    """
    Works on Unix (like Linux) systems only!
    """

    def __init__(self, moler_connection, cmd=['/bin/bash', '--norc', '--noprofile'], select_timeout=0.002,
                 read_buffer_size=4096, first_prompt=None, dimensions=(100, 300)):
        super(Terminal, self).__init__(moler_connection=moler_connection)
        self._cmd = cmd
        self._select_timeout = select_timeout
        self._read_buffer_size = read_buffer_size
        self.dimensions = dimensions
        self._terminal = None
        self.pulling_thread = None

        if first_prompt:
            self.prompt = first_prompt
        else:
            self.prompt = re.compile(r'^bash-\d+\.*\d*')

    def open(self, ):
        self._terminal = PtyProcessUnicode.spawn(self._cmd, dimensions=self.dimensions)
        done = Event()
        self.pulling_thread = TillDoneThread(target=self.pull_data,
                                             done_event=done,
                                             kwargs={'pulling_done': done})
        self.pulling_thread.start()

    def close(self, ):
        if self.pulling_thread:
            self.pulling_thread.join()
            self.pulling_thread = None
        super(Terminal, self).close()

        self._terminal.close()

    def send(self, cmd, newline="\n"):
        self._terminal.write(cmd)
        if newline:
            self._terminal.write(newline)

    def pull_data(self, pulling_done):
        shell_operable = False
        read_buffer = ""

        while not pulling_done.is_set():
            reads, _, _ = select.select([self._terminal.fd], [], [], self._select_timeout)
            if self._terminal.fd in reads:
                try:
                    data = self._terminal.read(self._read_buffer_size)
                    if shell_operable:
                        self.data_received(data)
                    else:
                        read_buffer = read_buffer + data
                        if re.search(self.prompt, read_buffer):
                            shell_operable = True
                            read_buffer = None
                except EOFError:
                    pulling_done.set()
