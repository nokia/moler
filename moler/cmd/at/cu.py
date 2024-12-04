# -*- coding: utf-8 -*-
"""
Run cu -l /dev/ttyS{} -s 19200 command.
"""

__author__ = 'Adam Klekowski'
__copyright__ = 'Copyright (C) 2020-2021, Nokia'
__email__ = 'adam.klekowski@nokia.com'

import re

from moler.cmd.commandchangingprompt import CommandChangingPrompt
from moler.cmd.unix.genericunix import r_cmd_failure_cause_alternatives
from moler.exceptions import ParsingDone
from moler.exceptions import CommandFailure


class Cu(CommandChangingPrompt):
    """
    Command to connect COM port using cu. Example output:

    $ cu -l /dev/ttyS21 -s 19200 -E -
    Connected.
    """
    def __init__(self, connection, serial_devname, prompt=None, newline_chars=None, target_newline="\n", runner=None, options=None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param serial_devname: name of serial device to be proxied (f.ex. 5).
        :param prompt: prompt where we start from
        :param newline_chars: Characters to split local lines - list.
        :param target_newline: Character to split remote lines.
        :param runner: Runner to run command.
        """
        self.serial_devname = serial_devname
        self.options = options
        proxy_prompt = r"Connected."
        super(Cu, self).__init__(connection=connection,
                                 prompt=prompt,
                                 newline_chars=newline_chars,
                                 expected_prompt=proxy_prompt,
                                 target_newline=target_newline,
                                 runner=runner)
        self.ret_required = False
        self._python_shell_exit_sent = False
        self.allowed_newline_after_prompt = True

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        if self.options:
            proxy_command = f"cu -l /dev/ttyS{self.serial_devname} -s 19200 -E '-' {self.options}"
        else:
            proxy_command = f"cu -l /dev/ttyS{self.serial_devname} -s 19200 -E '-'"
        return proxy_command

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None
        """
        try:
            self._check_command_failure(line)
        except ParsingDone:
            pass
        super(Cu, self).on_new_line(line=line, is_full_line=is_full_line)

    _re_command_fail = re.compile(r_cmd_failure_cause_alternatives, re.IGNORECASE)

    def _check_command_failure(self, line):
        """
        Checks if line has info about command failure.

        :param line: Line from device.
        :return: None
        :raise ParsingDone: if regex matches.
        """
        if self._regex_helper.search_compiled(self._re_command_fail, line):
            self.set_exception(CommandFailure(self, f"Found error regex in line '{line}'"))
            raise ParsingDone


COMMAND_OUTPUT_without_options = """
cu -l /dev/ttyS5 -s 19200 -E '-'
Connected.
"""

COMMAND_KWARGS_without_options = {"serial_devname": "5"}

COMMAND_RESULT_without_options = {}

COMMAND_OUTPUT_with_options = """
cu -l /dev/ttyS5 -s 19200 -E '-' -h
Connected.
"""

COMMAND_KWARGS_with_options = {"serial_devname": "5",
                               "options": "-h"}

COMMAND_RESULT_with_options = {}
