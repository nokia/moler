# -*- coding: utf-8 -*-
"""
Ssh-keygen command module.
"""

__author__ = 'Marcin Szlapa'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.szlapa@nokia.com'

import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Sshkeygen(GenericUnixCommand):

    def __init__(self, connection, prompt=None, newline_chars=None, options=None, file="/home/ute/.ssh/id_rsa",
                 passphrase=None, runner=None):
        """
        Constructs object for Unix command ssh-keygen.

        :param connection: Moler connection to device, terminal when command is executed.
        :param options: ssh-keygen command options.
        :param file: file in which to save the key.
        :param passphrase: passphrase
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Sshkeygen, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                        runner=runner)

        self.ret_required = False
        self.options = options
        self.file = file
        self.passphrase = passphrase

        self._file_name_sent = False
        self._overwrite_sent = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "ssh-keygen"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        else:
            cmd = "{}".format(cmd)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None.
        """
        try:
            self._parse_send_file_name(line)
            self._parse_overwrite(line)
            self._parse_passphrase(line)

            return super(Sshkeygen, self).on_new_line(line, is_full_line)
        except ParsingDone:
            pass

    # Enter passphrase (empty for no passphrase):
    _re_passphrase = re.compile(r"Enter passphrase \(empty for no passphrase\):")
    # Enter same passphrase again:
    _re_passphrase_2 = re.compile(r"Enter same passphrase again:")

    def _parse_passphrase(self, line):
        """
        Parses if waits for passphrase.

        :param line: Line from device.
        :return: None.
        :raises: ParsingDone if regex matches the line.
        """
        if re.search(Sshkeygen._re_passphrase, line) or re.search(Sshkeygen._re_passphrase_2, line):
            self.connection.sendline("")
            raise ParsingDone()

    # Enter file in which to save the key (/home/ute/.ssh/id_rsa):
    _re_send_file_name = re.compile(r"Enter file in which to save the key \(/home/ute/.ssh/id_rsa\):")

    def _parse_send_file_name(self, line):
        if re.search(Sshkeygen._re_send_file_name, line) and not self._file_name_sent:
            self.connection.sendline(self.file)

            self._file_name_sent = True
            raise ParsingDone

    # Overwrite (y/n)?
    _re_overwrite = re.compile(r"Overwrite (y/n)?")

    def _parse_overwrite(self, line):
        if re.search(Sshkeygen._re_overwrite, line) and not self._overwrite_sent:
            self.connection.sendline("y")

            self._overwrite_sent = True
            raise ParsingDone


COMMAND_OUTPUT = """"""

COMMAND_KWARGS = {

}

COMMAND_RESULT = {

}
