# -*- coding: utf-8 -*-
"""
cut command module.
"""

__author__ = "Marcin Szlapa"
__copyright__ = "Copyright (C) 2019, Nokia"
__email__ = "marcin.szlapa@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Cut(GenericUnixCommand):
    """Unix command cut."""

    def __init__(
        self,
        connection,
        options=None,
        path=None,
        prompt=None,
        newline_chars=None,
        runner=None,
    ):
        """
        Unix command cut.
        :param connection: moler connection to device, terminal when command is executed
        :param options: Options of unix du command
        :param path: file path
        :param prompt: expected prompt sending by device after command execution
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        """
        super(Cut, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.options = options
        self.path = path
        self.current_ret["LINES"] = []

    def build_command_string(self):
        """
        Build command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = "cut"
        if self.options:
            cmd = f"{cmd} {self.options}"
        if self.path:
            cmd = f"{cmd} {self.path}"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._parse_error(line)
                self._parse_cut(line)
            except ParsingDone:
                pass
        return super(Cut, self).on_new_line(line, is_full_line)

    # cut: you must specify a list of bytes, characters, or fields
    _re_parse_error = re.compile(r"cut:\s(?P<ERROR>.*)")

    def _parse_error(self, line):
        if self._regex_helper.search_compiled(Cut._re_parse_error, line):
            self.set_exception(
                CommandFailure(
                    self, f"ERROR: {self._regex_helper.group('ERROR')}"
                )
            )
            raise ParsingDone

    # # This file describes the network interfaces av

    def _parse_cut(self, line):
        if line:
            self.current_ret["LINES"].append(line)
            raise ParsingDone


COMMAND_OUTPUT_params = """host:~ # cut -d 'a' -f 1-3 /etc/network/interfaces
# This file describes the network interfaces av
# and how to activ

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
allow-hotplug enp0s3
iface enp0s3 inet dhcp
host:~ #"""

COMMAND_KWARGS_params = {"options": "-d 'a' -f 1-3", "path": "/etc/network/interfaces"}

COMMAND_RESULT_params = {
    "LINES": [
        "# This file describes the network interfaces av",
        "# and how to activ",
        "source /etc/network/interfaces.d/*",
        "# The loopback network interface",
        "auto lo",
        "iface lo inet loopback",
        "# The primary network interface",
        "allow-hotplug enp0s3",
        "iface enp0s3 inet dhcp",
    ]
}
