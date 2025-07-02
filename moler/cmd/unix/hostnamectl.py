# -*- coding: utf-8 -*-
"""
hostnamectl command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2025, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Hostnamectl(GenericUnixCommand):

    def __init__(self, connection, options=None, prompt=None, newline_chars=None, runner=None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param options: unix command options
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Hostnamectl, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.options = options

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = "hostnamectl"
        if self.options:
            cmd = f"{cmd} {self.options}"
            self.ret_required = False
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
                self._parse_name_value(line)
            except ParsingDone:
                pass
        return super(Hostnamectl, self).on_new_line(line, is_full_line)

    # Operating System: Ubuntu 22.04.5 LTS
    _re_name_value = re.compile(r"(?P<NAME>\S.*\S|\S+)\s*:\s*(?P<VALUE>\S.*\S|\S+)")

    def _parse_name_value(self, line):
        """
        Parse name and value from device.
        :param line: Line from device.
        :return: None but raises ParsingDone if line matches regex.
        """
        if self._regex_helper.search_compiled(Hostnamectl._re_name_value, line):
            self.current_ret[self._regex_helper.group("NAME")] = self._regex_helper.group("VALUE")
            raise ParsingDone()


COMMAND_OUTPUT = """hostnamectl
 Static hostname: hostname
       Icon name: computer-vm
         Chassis: vm
      Machine ID: 3b66248bea7c4c49bd998e0ec562ceb3
         Boot ID: 92bfb94e4b4e4d15315d421d4b8f4c32
  Virtualization: kvm
Operating System: Ubuntu 22.04.5 LTS
          Kernel: Linux 5.15.0-138-generic
    Architecture: x86-64
host:~ #"""

COMMAND_KWARGS = {}

COMMAND_RESULT = {
    "Static hostname": "hostname",
    "Icon name": "computer-vm",
    "Chassis": "vm",
    "Machine ID": "3b66248bea7c4c49bd998e0ec562ceb3",
    "Boot ID": "92bfb94e4b4e4d15315d421d4b8f4c32",
    "Virtualization": "kvm",
    "Operating System": "Ubuntu 22.04.5 LTS",
    "Kernel": "Linux 5.15.0-138-generic",
    "Architecture": "x86-64"
}


COMMAND_OUTPUT_set_hostname = """hostnamectl set-hostname new-hostname
host:~ #"""


COMMAND_KWARGS_set_hostname = {
    'options': 'set-hostname new-hostname'
}


COMMAND_RESULT_set_hostname = {}
