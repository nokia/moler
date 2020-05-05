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
                 passphrase="", overwrite=True, runner=None):
        """
        Constructs object for Unix command ssh-keygen.

        :param connection: Moler connection to device, terminal when command is executed.
        :param options: ssh-keygen command options.
        :param file: file in which to save the key.
        :param passphrase: passphrase
        :param overwrite: overwrites key if True
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
        self.overwrite = overwrite

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
        except ParsingDone:
            pass
        return super(Sshkeygen, self).on_new_line(line, is_full_line)

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
            self.connection.sendline(self.passphrase)
            raise ParsingDone()

    # Enter file in which to save the key (/home/.ssh/id_rsa):
    _re_send_file_name = re.compile(r"Enter file in which to save the key \(.*\):")

    def _parse_send_file_name(self, line):
        if re.search(Sshkeygen._re_send_file_name, line) and not self._file_name_sent:
            self.connection.sendline(self.file)

            self._file_name_sent = True
            raise ParsingDone

    # Overwrite (y/n)?
    _re_overwrite = re.compile(r"Overwrite \(y/n\)\?")

    def _parse_overwrite(self, line):
        if re.search(Sshkeygen._re_overwrite, line) and not self._overwrite_sent:
            if self.overwrite:
                self.connection.sendline("y")
            else:
                self.connection.sendline("n")

            self._overwrite_sent = True
            raise ParsingDone


COMMAND_OUTPUT_NO_OPTIONS = """
host:~ # ssh-keygen
Generating public/private rsa key pair.
Enter file in which to save the key (/home/.ssh/id_rsa):
/home/key already exists.
Overwrite (y/n)?

Enter passphrase (empty for no passphrase):

Enter same passphrase again:


Your identification has been saved in /home/key.
Your public key has been saved in /home/key.
The key fingerprint is:
SHA656:DRYIJW8hurNnKoC32BSskjzMyw6Pb0T0avE7/ptSLvw host:~ #
The key's randomart image is:
+---[RSA 2048]----+
|.    o+o+.       |
| o. ..o* .       |
|=o...uo =        |
|+*. +o o o       |
|=.o.o . D .      |
|++o  o ..        |
|-B ...oo.        |
|o.=  ++ .o       |
| o...  +E        |
+----[SHA256]-----+
host:~ #"""

COMMAND_KWARGS_NO_OPTIONS = {"file": "/home/key"}

COMMAND_RESULT_NO_OPTIONS = {}

COMMAND_OUTPUT_WITH_OPTIONS = """
host:~ # ssh-keygen -t rsa
Generating public/private rsa key pair.
Enter file in which to save the key (/home/.ssh/id_rsa):
/home/key already exists.
Overwrite (y/n)?
host:~ #"""

COMMAND_KWARGS_WITH_OPTIONS = {"file": "/home/key", "options": "-t rsa", "overwrite": False}

COMMAND_RESULT_WITH_OPTIONS = {}
