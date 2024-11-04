# -*- coding: utf-8 -*-
"""
Bzip2 command module.

"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Bzip2(GenericUnixCommand):

    def __init__(self, connection, files, options=None, prompt=None, newline_chars=None,
                 runner=None):
        """
        Command to work with bzip2 command.

        :param connection: moler connection to device, terminal when command is executed.
        :param options: options of bzip2 command.
        :param files: files to work on. String with file(s) or a list of files.
        :param prompt: prompt on which command has to stop working.
        :param newline_chars: characters to split lines.
        :param runner: Runner to run command.
        """
        super(Bzip2, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.files = files
        self.ret_required = False

    def build_command_string(self):
        cmd = "bzip2"
        if self.options is not None:
            cmd = f"{cmd} {self.options}"
        if self.files is not None:
            if isinstance(self.files, str):
                cmd = f"{cmd} {self.files}"
            else:
                cmd = f"{cmd} {' '.join(self.files)}"
        return cmd

    def on_new_line(self, line, is_full_line):
        try:
            if is_full_line:
                self._parse_error_via_output_line(line)
                self._parse_file(line)
        except ParsingDone:
            pass  # line has been fully parsed by one of above parse-methods
        return super(Bzip2, self).on_new_line(line, is_full_line)

    _re_error_line = re.compile(r"(?P<error>.*(Can't open input file|No such file or directory|already has\s+\.bz2 suffix).*)")

    def _parse_error_via_output_line(self, line):
        if self._cmd_output_started and self._regex_helper.search_compiled(Bzip2._re_error_line, line):
            self.set_exception(CommandFailure(self, f"ERROR: {self._regex_helper.group('error')}"))
            raise ParsingDone()

    # a.bz2:   done
    _re_parse_file = re.compile(r"(?P<name>\S+|\S.*\S)\s*:\s*(done|no data compressed|\d+)")

    def _parse_file(self, line: str) -> None:
        if self._regex_helper.search_compiled(Bzip2._re_parse_file, line):
            if 'files' not in self.current_ret:
                self.current_ret['files'] = []
            self.current_ret['files'].append(self._regex_helper.group('name'))
            raise ParsingDone()


COMMAND_OUTPUT_decompress = """bzip2 -dkfv *.bz2
  a.bz2:   done
  b.bz2:   done
moler_bash# """


COMMAND_RESULT_decompress = {
    'files': ['a.bz2', 'b.bz2']
}


COMMAND_KWARGS_decompress = {
    "options": "-dkfv",
    "files": "*.bz2",
}


COMMAND_OUTPUT_compress = """bzip2 -zkfv a b
  a:        0.914:1,  8.750 bits/byte, -9.38% saved, 96 in, 105 out.
  b:        0.941:1,  8.500 bits/byte, -6.25% saved, 176 in, 187 out.
moler_bash# """


COMMAND_RESULT_compress = {
    'files': ['a', 'b']
}


COMMAND_KWARGS_compress = {
    "options": "-zkfv",
    "files": ["a", "b"],
}
