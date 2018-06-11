__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import re
import select
from threading import Event

from ptyprocess import PtyProcessUnicode

from moler.cmd.unix.bash import Bash
from moler.connection import ObservableConnection
from moler.io.raw import TillDoneThread


class Terminal(ObservableConnection):
    """
    Works on Unix (like Linux) systems only!
    """

    def __init__(self, cmd='/bin/bash', bash_cmd='TERM=xterm-mono bash', select_timeout=0.002, read_buffer_size=4096,
                 first_prompt=None):
        self._cmd = [cmd]
        self._select_timeout = select_timeout
        self._read_buffer_size = read_buffer_size
        self._terminal = None
        self._exit = False
        self._terminal = PtyProcessUnicode.spawn(self._cmd)
        if first_prompt:
            self.prompt = first_prompt
        else:
            self.prompt = re.compile(r'^[^<]*[\$|%|#|>|~|:]\s*')
        # Thread.__init__(self)
        ObservableConnection.__init__(self)
        self.pulling_thread = None
        done = Event()
        self.pulling_thread = TillDoneThread(target=self._main_loop,
                                             done_event=done,
                                             kwargs={'pulling_done': done})
        self.pulling_thread.start()
        cmd = Bash(connection=self, bash=bash_cmd)
        cmd.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # reraise exceptions if any

    def close(self, ):
        if self.pulling_thread:
            self.pulling_thread.join()
            self.pulling_thread = None
        super(Terminal, self).close()

    def send(self, cmd, newline="\n"):
        self._terminal.write(cmd)
        if newline:
            self._terminal.write(newline)

    def run(self, ):
        self._main_loop()
        self._terminal.wait()
        self._terminal.close()

    def _main_loop(self, pulling_done):
        was_first_prompt = False
        read_buffer = ""
        while not pulling_done.is_set():
            reads, _, _ = select.select([self._terminal.fd], [], [], self._select_timeout)
            if self._terminal.fd in reads:
                if was_first_prompt:
                    if not self._read_from_terminal():
                        break
                else:
                    read_line = self._terminal.read(self._read_buffer_size)
                    read_buffer = read_buffer + read_line
                    if re.search(self.prompt, read_buffer):
                        was_first_prompt = True
                        read_buffer = None

            if self._exit:
                self._exit = False
                break

    def _read_from_terminal(self):
        try:
            self.data_received(self._terminal.read(self._read_buffer_size))
        except EOFError:
            return False

        return True
