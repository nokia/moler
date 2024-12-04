# -*- coding: utf-8 -*-
"""
adb shell command module.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import re

from moler.cmd.commandchangingprompt import CommandChangingPrompt
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
from moler.cmd.unix.genericunix import r_cmd_failure_cause_alternatives
from moler.helpers import remove_all_known_special_chars


class AdbShell(CommandChangingPrompt):
    re_generated_prompt = r'^adb_shell@{} \$'

    def __init__(self, connection, serial_number=None, prompt=None, expected_prompt=None,
                 newline_chars=None, target_newline="\n", runner=None, set_timeout=None,
                 allowed_newline_after_prompt=False, set_prompt=None, prompt_after_login=None,
                 prompt_from_serial_number=False):
        """
        Moler class of Unix command adb shell.

        It is intended to enter shell and not run commands via shell like 'adb shell ls -l'  # TODO: AdbShellExecute ?

        :param connection: moler connection to device, terminal when command is executed.
        :param serial_number: SN of selected device as seen on 'adb devices'  # TODO: device_serial_number?
        :param prompt: start prompt.
        :param expected_prompt: final prompt.
        :param newline_chars: Characters to split lines.
        :param target_newline: newline chars on root user.
        :param runner: Runner to run command.
        :param set_timeout: Command to set timeout after adb shell success.
        :param allowed_newline_after_prompt: If True then newline chars may occur after expected (target) prompt
        :param set_prompt: Command to set prompt after adb shell success.
        :param prompt_after_login: prompt after login before send export PS1. If you do not change prompt exporting PS1
         then leave it None.
        :param prompt_from_serial_number: Generate expected_prompt from serial_number.
        """
        if prompt_from_serial_number and (not expected_prompt):
            if not prompt_after_login:
                prompt_after_login = self._re_default_prompt
            if serial_number and (not set_prompt):
                set_prompt = fr'export PS1="adb_shell@{serial_number} \$ "'
                expected_prompt = re.compile(self.re_generated_prompt.format(serial_number))  # pylint: disable=consider-using-f-string
        super(AdbShell, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                       runner=runner, expected_prompt=expected_prompt, set_timeout=set_timeout,
                                       set_prompt=set_prompt, target_newline=target_newline,
                                       allowed_newline_after_prompt=allowed_newline_after_prompt,
                                       prompt_after_login=prompt_after_login)
        self.serial_number = serial_number
        self.ret_required = False
        self.remove_all_known_special_chars_from_terminal_output = True

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "adb shell"
        if self.serial_number:
            cmd = f"adb -s {self.serial_number} shell"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None
        """
        try:
            self._command_failure(line)
        except ParsingDone:
            pass
        super(AdbShell, self).on_new_line(line=line, is_full_line=is_full_line)

    _re_command_fail = re.compile(f"{r_cmd_failure_cause_alternatives}|^error:", re.IGNORECASE)

    def _command_failure(self, line):
        """
        Checks if line has info about command failure.

        :param line: Line from device.
        :return: None
        :raise ParsingDone: if regex matches.
        """
        if self._regex_helper.search_compiled(AdbShell._re_command_fail, line):
            self.set_exception(CommandFailure(self, f"Found error regex in line '{line}'"))
            raise ParsingDone

    def _decode_line(self, line):
        """
        Method to delete new line chars and other chars we don not need to parse in on_new_line (color escape character)

        :param line: Line with special chars, raw string from device
        :return: line without special chars.
        """
        if self.remove_all_known_special_chars_from_terminal_output:
            line = remove_all_known_special_chars(line)
        return line


COMMAND_OUTPUT_one_device = """
xyz@debian ~$ adb shell
shell@adbhost:/ $ """

COMMAND_KWARGS_one_device = {
    'expected_prompt': r'shell@adbhost:/ \$'
}

COMMAND_RESULT_one_device = {}

COMMAND_OUTPUT_selected_device = """
xyz@debian ~$ adb -s f57e6b77 shell
shell@adbhost:/ $ """

COMMAND_KWARGS_selected_device = {
    'serial_number': 'f57e6b77',
    'expected_prompt': r'shell@adbhost:/ \$'
}

COMMAND_RESULT_selected_device = {}

COMMAND_OUTPUT_serial_number_generated_prompt = r"""
xyz@debian ~$ adb -s f57e6b77 shell
shell@adbhost:/ $
shell@adbhost:/ $ export PS1="adb_shell@f57e6b77 \$ "
adb_shell@f57e6b77 $ """

COMMAND_KWARGS_serial_number_generated_prompt = {
    'serial_number': 'f57e6b77',
    'prompt_from_serial_number': True
}

COMMAND_RESULT_serial_number_generated_prompt = {}
