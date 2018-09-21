__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import os
import re
import select
from threading import Event

from ptyprocess import PtyProcessUnicode

from moler.io.io_connection import IOConnection
from moler.io.raw import TillDoneThread


class ThreadedTerminal(IOConnection):
    """
    Works on Unix (like Linux) systems only!

    ThreadedTerminal is shell working under Pty
    """

    def __init__(self, moler_connection, cmd=None, select_timeout=0.002,
                 read_buffer_size=4096, first_prompt=None, dimensions=(100, 300)):
        super(ThreadedTerminal, self).__init__(moler_connection=moler_connection)
        self._select_timeout = select_timeout
        self._read_buffer_size = read_buffer_size
        self.dimensions = dimensions
        self._terminal = None
        self.pulling_thread = None
        self._shell_operable = Event()
        if cmd is None:
            cmd = ['/bin/bash', '--init-file']
        self._cmd = ThreadedTerminal._build_bash_command(cmd)

        if first_prompt:
            self.prompt = first_prompt
        else:
            self.prompt = r'^moler_bash#'

    def open(self):
        """Open ThreadedTerminal connection & start thread pulling data from it."""
        if not self._terminal:
            self._terminal = PtyProcessUnicode.spawn(self._cmd, dimensions=self.dimensions)
            done = Event()
            self.pulling_thread = TillDoneThread(target=self.pull_data,
                                                 done_event=done,
                                                 kwargs={'pulling_done': done})
            self.pulling_thread.start()
            self._shell_operable.wait(timeout=2)

    def close(self):
        """Close ThreadedTerminal connection & stop pulling thread."""
        if self.pulling_thread:
            self.pulling_thread.join()
            self.pulling_thread = None
        super(ThreadedTerminal, self).close()

        if self._terminal and self._terminal.isalive():
            self._terminal.close()
            self._terminal = None
            self._notify_on_disconnect()

    def send(self, data):
        """Write data into ThreadedTerminal connection."""
        self._terminal.write(data)

    def pull_data(self, pulling_done):
        """Pull data from ThreadedTerminal connection."""
        read_buffer = ""

        while not pulling_done.is_set():
            reads, _, _ = select.select([self._terminal.fd], [], [], self._select_timeout)
            if self._terminal.fd in reads:
                try:
                    data = self._terminal.read(self._read_buffer_size)
                    if self._shell_operable.is_set():
                        self.data_received(data)
                    else:
                        read_buffer = read_buffer + data
                        if re.search(self.prompt, read_buffer, re.MULTILINE):
                            self._notify_on_connect()
                            self._shell_operable.set()
                            data = re.sub(self.prompt, '', read_buffer, re.MULTILINE)
                            self.data_received(data)
                except EOFError:
                    self._notify_on_disconnect()
                    pulling_done.set()

    @staticmethod
    def _build_bash_command(bash_cmd):
        abs_path = os.path.dirname(__file__)
        init_file_path = [os.path.join(abs_path, "..", "..", "config", "bash_config")]

        return bash_cmd + init_file_path
