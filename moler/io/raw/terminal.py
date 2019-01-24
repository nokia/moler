# -*- coding: utf-8 -*-
__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import codecs
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

    def __init__(self, moler_connection, cmd="/bin/bash", select_timeout=0.002,
                 read_buffer_size=4096, first_prompt=r'[%$#]+', target_prompt=r'^moler_bash#',
                 set_prompt_cmd='export PS1="moler_bash# "\n', dimensions=(100, 300)):
        """
        :param moler_connection: Moler's connection to join with
        :param cmd: command to run terminal
        :param select_timeout: timeout for reading data from terminal
        :param read_buffer_size: buffer for reading data from terminal
        :param first_prompt: default terminal prompt on host where Moler is starting
        :param target_prompt: new prompt which will be set on terminal
        :param set_prompt_cmd: command to change prompt with new line char on the end of string
        :param dimensions: dimensions of the psuedoterminal
        """
        super(ThreadedTerminal, self).__init__(moler_connection=moler_connection)
        self._terminal = None
        self._shell_operable = Event()
        self._export_sent = False
        self.pulling_thread = None

        self._select_timeout = select_timeout
        self._read_buffer_size = read_buffer_size
        self.dimensions = dimensions
        self.first_prompt = first_prompt
        self.target_prompt = target_prompt
        self._cmd = [cmd]
        self.set_prompt_cmd = set_prompt_cmd

    def open(self):
        """Open ThreadedTerminal connection & start thread pulling data from it."""
        ret = super(ThreadedTerminal, self).open()

        if not self._terminal:
            self._terminal = PtyProcessUnicode.spawn(self._cmd, dimensions=self.dimensions)
            # need to not replace not unicode data instead of raise exception
            self._terminal.decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')

            done = Event()
            self.pulling_thread = TillDoneThread(target=self.pull_data,
                                                 done_event=done,
                                                 kwargs={'pulling_done': done})
            self.pulling_thread.start()
            retry = 0
            is_operable = False

            while (retry < 3) and (not is_operable):
                is_operable = self._shell_operable.wait(timeout=1)
                if not is_operable:
                    self.logger.warning("Terminal open but not fully operable yet")
                    self._terminal.write('\n')
                    retry += 1

        return ret

    def close(self):
        """Close ThreadedTerminal connection & stop pulling thread."""
        if self.pulling_thread:
            self.pulling_thread.join()
            self.pulling_thread = None
        super(ThreadedTerminal, self).close()

        if self._terminal and self._terminal.isalive():
            self._terminal.close(force=True)
            self._terminal = None
            self._notify_on_disconnect()

    def send(self, data):
        """Write data into ThreadedTerminal connection."""
        self._terminal.write(data)

    def pull_data(self, pulling_done):
        """Pull data from ThreadedTerminal connection."""
        read_buffer = ""
        reads = []

        while not pulling_done.is_set():
            try:
                reads, _, _ = select.select([self._terminal.fd], [], [], self._select_timeout)
            except ValueError as exc:
                self.logger.warning("'{}: {}'".format(exc.__class__, exc))
                self._notify_on_disconnect()
                pulling_done.set()

            if self._terminal.fd in reads:
                try:
                    data = self._terminal.read(self._read_buffer_size)

                    if self._shell_operable.is_set():
                        self.data_received(data)
                    else:
                        read_buffer = read_buffer + data
                        if re.search(self.target_prompt, read_buffer, re.MULTILINE):
                            self._notify_on_connect()
                            self._shell_operable.set()
                            data = re.sub(self.target_prompt, '', read_buffer, re.MULTILINE)
                            self.data_received(data)
                        elif not self._export_sent and re.search(self.first_prompt, read_buffer, re.MULTILINE):
                            self.send(self.set_prompt_cmd)
                            self._export_sent = True
                except EOFError:
                    self._notify_on_disconnect()
                    pulling_done.set()
