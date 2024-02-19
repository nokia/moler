# -*- coding: utf-8 -*-
"""
Uname command module.
"""

__author__ = "Agnieszka Bylica"
__copyright__ = "Copyright (C) 2018, Nokia"
__email__ = "agnieszka.bylica@nokia.com"


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Uname(GenericUnixCommand):
    def __init__(
        self, connection, options=None, prompt=None, newline_chars=None, runner=None
    ):
        super(Uname, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.options = options
        self.current_ret["RESULT"] = []

    def build_command_string(self):
        cmd = "uname"
        if self.options:
            cmd = f"{cmd} {self.options}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_error(line)
                self._parse(line)
            except ParsingDone:
                pass
        return super(Uname, self).on_new_line(line, is_full_line)

    _re_invalid_option = re.compile(
        r"uname:\s(invalid|unknown)\soption\s(?P<OPTION>.*)", re.IGNORECASE
    )
    _re_command_fail = re.compile(
        r"uname:\sextra\soperand\s(?P<COMMAND>.*)", re.IGNORECASE
    )

    def _command_error(self, line):
        if self._regex_helper.search_compiled(Uname._re_invalid_option, line):
            self.set_exception(
                CommandFailure(
                    self, f"ERROR: {self._regex_helper.group('OPTION')}"
                )
            )
            raise ParsingDone

        elif self._regex_helper.search_compiled(Uname._re_command_fail, line):
            self.set_exception(
                CommandFailure(
                    self, f"ERROR: {self._regex_helper.group('COMMAND')}"
                )
            )
            raise ParsingDone

    def _parse(self, line):
        self.current_ret["RESULT"].append(line)
        raise ParsingDone


# -----------------------------------------------------------------------------
# Following documentation is required for library CI.
# It is used to perform command self-test.
# Parameters: -a ; -s
# -----------------------------------------------------------------------------


COMMAND_OUTPUT_ver_execute = """
xyz@debian:~$ uname -a
Linux debian 4.9.0-6-amd64 #1 SMP
Debian 4.9.88-1+deb9u1 (2018-05-07) x86_64 GNU/Linux
xyz@debian:~$"""

COMMAND_KWARGS_ver_execute = {"options": "-a"}

COMMAND_RESULT_ver_execute = {
    "RESULT": [
        "Linux debian 4.9.0-6-amd64 #1 SMP",
        "Debian 4.9.88-1+deb9u1 (2018-05-07) x86_64 GNU/Linux",
    ]
}

COMMAND_OUTPUT_without_option = """
xyz@debian:~$ uname
Linux
xyz@debian:~$"""

COMMAND_KWARGS_without_option = {"options": None}

COMMAND_RESULT_without_option = {"RESULT": ["Linux"]}
