# -*- coding: utf-8 -*-
"""
Unrar command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Unrar(GenericUnixCommand):

    def __init__(self, connection, options, archive_file, prompt=None, newline_chars=None,
                 runner=None):
        """
        Command to work with unrar command.

        :param connection: moler connection to device, terminal when command is executed.
        :param options: options of unrar command.
        :param archive_file: archive file to work on.
        :param prompt: prompt on which command has to stop working.
        :param newline_chars: characters to split lines.
        :param runner: Runner to run command.
        """
        super(Unrar, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.archive_file = archive_file
        self.ret_required = False
        self._all_sent = False

    def build_command_string(self):
        cmd = f"unrar {self.options} {self.archive_file}"
        return cmd

    def on_new_line(self, line, is_full_line):
        try:
            self._parse_all(line=line)
            if is_full_line:
                self._parse_error_via_output_line(line)
                self._parse_file_name(line)
        except ParsingDone:
            pass  # line has been fully parsed by one of above parse-methods
        if is_full_line:
            self._all_sent = False
        return super(Unrar, self).on_new_line(line, is_full_line)

    _re_error_line = re.compile(r'(?P<error>.*(Cannot open|No such file or directory|No files to extract).*)')

    def _parse_error_via_output_line(self, line):
        if self._cmd_output_started and self._regex_helper.search_compiled(Unrar._re_error_line, line):
            self.set_exception(CommandFailure(self, f"ERROR: {self._regex_helper.group('error')}"))
            raise ParsingDone()

    # Extracting  a                                                         OK
    _re_file_name = re.compile(r"Extracting\s+(?P<filename>\S+|\S.*\S)\s+OK")

    def _parse_file_name(self, line: str) -> None:
        if self._regex_helper.search_compiled(Unrar._re_file_name, line):
            if 'files' not in self.current_ret:
                self.current_ret['files'] = []
            self.current_ret['files'].append(self._regex_helper.group('filename'))
            raise ParsingDone()

    # [Y]es, [N]o, [A]ll, n[E]ver, [R]ename, [Q]uit
    _re_all = re.compile(r"\[Y\]es, \[N\]o, \[A\]ll, n\[E\]ver, \[R\]ename, \[Q\]uit")

    def _parse_all(self, line: str) -> None:
        if self._all_sent is False and self._regex_helper.search_compiled(Unrar._re_all, line):
            self.connection.send("a\n")
            self._all_sent = True
            raise ParsingDone()


COMMAND_OUTPUT = """unrar e arch.rar

UNRAR 6.21 freeware      Copyright (c) 1993-2023 Alexander Roshal


Extracting from arch.rar


Would you like to replace the existing file a
     0 bytes, modified on 2024-07-24 13:17
with a new one
     0 bytes, modified on 2024-07-24 13:17

[Y]es, [N]o, [A]ll, n[E]ver, [R]ename, [Q]uit A

Extracting  a                                                         OK
Extracting  b                                                         OK
All OK
moler_bash# """


COMMAND_RESULT = {
    "files": ["a", "b"],
}


COMMAND_KWARGS = {
    "options": "e",
    "archive_file": "arch.rar",
}
