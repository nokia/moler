# -*- coding: utf-8 -*-
__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import codecs
import re
import select
import datetime
from threading import Event

from ptyprocess import PtyProcessUnicode

from moler.io.io_connection import IOConnection
from moler.io.raw import TillDoneThread
from moler.helpers import remove_all_known_special_chars
from moler.helpers import all_chars_to_hex
from moler.helpers import non_printable_chars_to_hex


class ThreadedTerminal(IOConnection):
    """
    Works on Unix (like Linux) systems only!

    ThreadedTerminal is shell working under Pty
    """

    def __init__(self, moler_connection, cmd="/bin/bash", select_timeout=0.002,
                 read_buffer_size=4096, first_prompt=r'[%$#]+', target_prompt=r'moler_bash#',
                 set_prompt_cmd='export PS1="moler_bash# "\n', dimensions=(100, 300)):
        """  # TODO: # 'export PS1="moler_bash\\$ "\n'  would give moler_bash# for root and moler_bash$ for user
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
        self.debug_hex_on_non_printable_chars = False  # Set True to log incoming non printable chars as hex.
        self.debug_hex_on_all_chars = False  # Set True to log incoming data as hex.
        self._terminal = None
        self._shell_operable = Event()
        self._export_sent = False
        self.pulling_thread = None
        self.read_buffer = ""

        self._select_timeout = select_timeout
        self._read_buffer_size = read_buffer_size
        self.dimensions = dimensions
        self.first_prompt = first_prompt
        self.target_prompt = target_prompt
        self._cmd = [cmd]
        self.set_prompt_cmd = set_prompt_cmd
        self._re_set_prompt_cmd = re.sub("['\"].*['\"]", "", self.set_prompt_cmd.strip())

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

            while (retry < 10) and (not is_operable):
                is_operable = self._shell_operable.wait(timeout=1)
                if not is_operable:
                    self.logger.warning(
                        "Terminal open but not fully operable yet.\nREAD_BUFFER: '{}'".format(
                            self.read_buffer.encode("UTF-8", "replace")))
                    self._terminal.write('\n')
                    retry += 1

        return ret

    def close(self):
        """Close ThreadedTerminal connection & stop pulling thread."""
        if self.pulling_thread:
            self.pulling_thread.join()
            self.pulling_thread = None
        self.moler_connection.shutdown()
        super(ThreadedTerminal, self).close()

        if self._terminal and self._terminal.isalive():
            self._terminal.close(force=True)
            self._terminal = None
            self._notify_on_disconnect()

    def send(self, data):
        """Write data into ThreadedTerminal connection."""
        if self._terminal:
            self._terminal.write(data)

    def pull_data(self, pulling_done):
        """Pull data from ThreadedTerminal connection."""
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
                    if self.debug_hex_on_all_chars:
                        self.logger.debug("incoming data: '{}'.".format(all_chars_to_hex(data)))
                    if self.debug_hex_on_non_printable_chars:
                        self.logger.debug("incoming data: '{}'.".format(non_printable_chars_to_hex(data)))

                    if self._shell_operable.is_set():
                        self.data_received(data=data, recv_time=datetime.datetime.now())
                    else:
                        self._verify_shell_is_operable(data)
                except EOFError:
                    self._notify_on_disconnect()
                    pulling_done.set()

    def _verify_shell_is_operable(self, data):
        self.read_buffer = self.read_buffer + data
        lines = self.read_buffer.splitlines()

        for line in lines:
            line = remove_all_known_special_chars(line)
            if not re.search(self._re_set_prompt_cmd, line) and re.search(self.target_prompt, line):
                self._notify_on_connect()
                self._shell_operable.set()
                data = re.sub(self.target_prompt, '', self.read_buffer, re.MULTILINE)
                self.data_received(data=data, recv_time=datetime.datetime.now())
            elif not self._export_sent and re.search(self.first_prompt, self.read_buffer, re.MULTILINE):
                self.send(self.set_prompt_cmd)
                self._export_sent = True
