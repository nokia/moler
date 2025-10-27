# -*- coding: utf-8 -*-
"""
Rm command module.
"""

__author__ = 'Bartosz Odziomek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2025, Nokia'
__email__ = 'bartosz.odziomek@nokia.com, marcin.usielski@nokia.com'

from moler.helpers import copy_list
from moler.cmd.unix.genericunix import GenericUnixCommand, cmd_failure_causes
import re


class Rm(GenericUnixCommand):
    def __init__(self, connection, file, options=None, prompt=None, newline_chars=None, runner=None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param file: Path to file to remove.
        :param options: Unix options of rm command.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Rm, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        self.file = file
        self.options = options
        self.ret_required = False
        _cmd_failure_causes = copy_list(cmd_failure_causes)
        _cmd_failure_causes.append(r"cannot remove\s*'.*':\s*Permission denied")
        r_cmd_failure_cause_alternatives = "|".join(_cmd_failure_causes)
        self.re_fail = re.compile(r_cmd_failure_cause_alternatives, re.IGNORECASE)

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = f"rm {self.file}"
        if self.options:
            cmd = f"rm {self.options} {self.file}"

        return cmd


COMMAND_OUTPUT_NO_OPTIONS = """
user@server:~> rm test.txt
user@server:~>
"""

COMMAND_RESULT_NO_OPTIONS = {
}

COMMAND_KWARGS_NO_OPTIONS = {
    "file": "test.txt",
}

COMMAND_OUTPUT_WITH_OPTIONS = """
user@server:~> rm -R test.txt
user@server:~>
"""

COMMAND_RESULT_WITH_OPTIONS = {
}

COMMAND_KWARGS_WITH_OPTIONS = {
    "file": "test.txt",
    "options": "-R"
}
