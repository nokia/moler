# -*- coding: utf-8 -*-
"""
Run plink -serial command
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import re

from moler.cmd.commandchangingprompt import CommandChangingPrompt
from moler.cmd.unix.genericunix import r_cmd_failure_cause_alternatives
from moler.exceptions import ParsingDone
from moler.exceptions import CommandFailure


class PlinkSerial(CommandChangingPrompt):

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
        proxy_prompt = r"{}>".format(serial_devname)
        super(PlinkSerial, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                          expected_prompt=proxy_prompt, target_newline=target_newline, runner=runner)
        self.ret_required = False
        self._python_shell_exit_sent = False
        self.allowed_newline_after_prompt = True

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        # we pipe via awk because:
        # 1) we want entry prompt like 'COM5> port READY' (plink -serial attaches AT console which is silent/no prompt)
        # 2) we want to remove all terminal ctrl codes (especially on cygwin + winpty environment)
        # 3) we need to simulate Ctrl-C output after plink completion to allow using ctrl_c unix command to stop plink
        awk_cmd = 'awk \'BEGIN {print "COM5> port READY"} {print} END {print "^C"}\''
        proxy_command = "plink -serial {} |& {}".format(self.serial_devname, awk_cmd)
        return proxy_command

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None.
        """
        try:
            self._check_command_failure(line)
        except ParsingDone:
            pass
        super(PlinkSerial, self).on_new_line(line=line, is_full_line=is_full_line)

    _re_command_fail = re.compile(r_cmd_failure_cause_alternatives, re.IGNORECASE)

    def _check_command_failure(self, line):
        """
        Checks if line has info about command failure.

        :param line: Line from device.
        :return: None
        :raise ParsingDone: if regex matches.
        """
        if self._regex_helper.search_compiled(self._re_command_fail, line):
            self.set_exception(CommandFailure(self, "Found error regex in line '{}'".format(line)))
            raise ParsingDone


COMMAND_OUTPUT = """
plink -serial COM5 |& awk -v entry_prompt="COM5> port READY" -v ctrlc="^C" -v exit_prompt="${PS1@P}" 'BEGIN {print entry_prompt} {print} END {print ctrlc; print exit_prompt}'
COM5> port READY"""

COMMAND_KWARGS = {"serial_devname": "COM5"}

COMMAND_RESULT = {}
