# -*- coding: utf-8 -*-
"""
Useradd command module.
"""

__author__ = "Agnieszka Bylica"
__copyright__ = "Copyright (C) 2018, Nokia"
__email__ = "agnieszka.bylica@nokia.com"


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Useradd(GenericUnixCommand):
    def __init__(
        self,
        connection,
        prompt=None,
        newline_chars=None,
        runner=None,
        options=None,
        defaults=False,
        user=None,
    ):
        super(Useradd, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )

        # Parameters defined by calling the command
        self.options = options
        self.defaults = defaults
        self.user = user

        # Internal variables
        self.current_ret["RESULT"] = []

    def build_command_string(self):
        cmd = "useradd"
        if self.defaults:
            cmd = f"{cmd} -D"
            if self.options:
                cmd = f"{cmd} {self.options}"
        elif self.user:
            if self.options:
                cmd = f"{cmd} {self.options}"
            cmd = f"{cmd} {self.user}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_error(line)
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Useradd, self).on_new_line(line, is_full_line)

    def _parse_line(self, line):
        self.current_ret["RESULT"].append(line)
        raise ParsingDone

    _re_error = re.compile(
        r"Usage:\suseradd\s\[options\]\sLOGIN(?P<ERROR>.*)", re.IGNORECASE
    )
    _re_invalid_syntax = re.compile(r"useradd:\s(?P<ERROR>.*)", re.IGNORECASE)

    def _command_error(self, line):
        if self._regex_helper.search_compiled(Useradd._re_error, line):
            self.set_exception(
                CommandFailure(
                    self, f"ERROR: {self._regex_helper.group('ERROR')}"
                )
            )
            raise ParsingDone
        elif self._regex_helper.search_compiled(Useradd._re_invalid_syntax, line):
            self.set_exception(CommandFailure(self, "ERROR: invalid command syntax"))
            raise ParsingDone


COMMAND_OUTPUT = """xyz@debian:~$ useradd -D
GROUP=100
HOME=/home
INACTIVE=-1
EXPIRE=
SHELL=/bin/sh
SKEL=/etc/skel
CREATE_MAIL_SPOOL=no
xyz@debian:~$"""

COMMAND_KWARGS = {"defaults": True}

COMMAND_RESULT = {
    "RESULT": [
        "GROUP=100",
        "HOME=/home",
        "INACTIVE=-1",
        "EXPIRE=",
        "SHELL=/bin/sh",
        "SKEL=/etc/skel",
        "CREATE_MAIL_SPOOL=no",
    ]
}


COMMAND_OUTPUT_pwd = """xyz@debian:~$ useradd -p 1234 abc
xyz@debian:~$"""

COMMAND_KWARGS_pwd = {"user": "abc", "options": "-p 1234"}

COMMAND_RESULT_pwd = {"RESULT": []}
