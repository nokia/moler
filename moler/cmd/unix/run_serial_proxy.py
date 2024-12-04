# -*- coding: utf-8 -*-
"""
Run moler_serial_proxy command
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import re

from moler.cmd.commandchangingprompt import CommandChangingPrompt
from moler.cmd.unix.genericunix import r_cmd_failure_cause_alternatives
from moler.exceptions import ParsingDone
from moler.exceptions import CommandFailure


class RunSerialProxy(CommandChangingPrompt):

    def __init__(self, connection, serial_devname, prompt=None, newline_chars=None, target_newline="\n", runner=None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param serial_devname: name of serial device to be proxied (f.ex. COM5, ttyS4).
        :param prompt: prompt where we start from
        :param newline_chars: Characters to split local lines - list.
        :param target_newline: Character to split remote lines.
        :param runner: Runner to run command.
        """
        self.serial_devname = serial_devname
        proxy_prompt = fr"{serial_devname}>"
        super(RunSerialProxy, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                             runner=runner, expected_prompt=proxy_prompt, target_newline=target_newline)
        self.ret_required = False
        self._python_shell_exit_sent = False
        self.allowed_newline_after_prompt = True

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        proxy_command = f"python -i moler_serial_proxy.py {self.serial_devname}"
        return proxy_command

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None
        """
        try:
            self._exit_from_python_shell(line)
            self._check_command_failure(line)
        except ParsingDone:
            pass
        super(RunSerialProxy, self).on_new_line(line=line, is_full_line=is_full_line)

    # error in python code of proxy - will show Traceback on python shell
    _re_command_fail = re.compile(fr"{r_cmd_failure_cause_alternatives}|traceback", re.IGNORECASE)

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

    def _exit_from_python_shell(self, line):
        """
        Exit from python after detecting python interactive shell

        :param line: Line to process
        :return: None
        """
        if (not self._python_shell_exit_sent) and self._in_python_shell(line):
            self.connection.send(f"exit(){self.target_newline}")
            self._python_shell_exit_sent = True
            raise ParsingDone

    _re_python_prompt = re.compile(r'>>>\s')

    def _in_python_shell(self, line):
        return self._regex_helper.search_compiled(self._re_python_prompt, line)


COMMAND_OUTPUT = """
python -i moler_serial_proxy.py COM5
starting COM5 proxy at PC10 ...
PC10  opening serial port COM5
ATE1
OK
PC10:COM5> """

COMMAND_KWARGS = {"serial_devname": "COM5"}

COMMAND_RESULT = {}
