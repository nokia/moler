# -*- coding: utf-8 -*-
"""
Sed command module.
"""

__author__ = "Agnieszka Bylica, Marcin Usielski, Michal Ernst"
__copyright__ = "Copyright (C) 2018-2019, Nokia"
__email__ = (
    "agnieszka.bylica@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com"
)

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Sed(GenericUnixCommand):
    def __init__(
        self,
        connection,
        input_files,
        prompt=None,
        newline_chars=None,
        runner=None,
        options=None,
        scripts=None,
        script_files=None,
        output_file=None,
    ):
        super(Sed, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )

        # Parameters defined by calling the command
        self.options = options  # string or None
        self.scripts = scripts  # list of strings or None
        self.script_files = script_files  # list of strings or None
        self.input_files = input_files  # list of strings
        self.output_file = output_file  # string or None

        # Other parameters
        self.current_ret["RESULT"] = []

    def build_command_string(self):
        cmd = "sed"
        if self.options:
            cmd = f"{cmd} {self.options}"
        if self.scripts:
            for script in self.scripts:
                cmd = f"{cmd} -e '{script}'"
        if self.script_files:
            for script_file in self.script_files:
                cmd = f"{cmd} -f {script_file}"
        if self.input_files:
            for in_file in self.input_files:
                cmd = f"{cmd} {in_file}"
        if self.output_file:
            cmd = f"{cmd} > {self.output_file}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_error(line)
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Sed, self).on_new_line(line, is_full_line)

    _re_command_error = re.compile(r"sed:\s(?P<ERROR>.*)", re.IGNORECASE)

    def _command_error(self, line):
        if self._regex_helper.search_compiled(Sed._re_command_error, line):
            self.set_exception(
                CommandFailure(
                    self, f"ERROR {self._regex_helper.group('ERROR')}"
                )
            )
            raise ParsingDone

    def _parse_line(self, line):
        self.current_ret["RESULT"].append(line)
        raise ParsingDone

    def _is_input_file(self):
        is_empty = True
        for file in self.input_files:
            if file and not file.isspace():
                is_empty = False
        if is_empty:
            raise CommandFailure(
                self, f"No input file given in: {self.input_files}"
            )

    def _validate_start(self, *args, **kwargs):
        super(Sed, self)._validate_start(*args, **kwargs)
        # _validate_start is called before running command on connection, so we raise exception instead of setting it
        self._is_input_file()


COMMAND_OUTPUT = """xyz@debian:~$ sed -e 's/a/A/' old old2 > new
xyz@debian:~$"""

COMMAND_KWARGS = {
    "scripts": ["s/a/A/"],
    "output_file": "new",
    "input_files": ["old", "old2"],
}

COMMAND_RESULT = {"RESULT": []}

COMMAND_OUTPUT_to_stdout = """xyz@debian:~$ sed -e 's/a/A/' old old2
Apple
peAr
plum
xyz@debian:~$"""

COMMAND_KWARGS_to_stdout = {"scripts": ["s/a/A/"], "input_files": ["old", "old2"]}

COMMAND_RESULT_to_stdout = {"RESULT": ["Apple", "peAr", "plum"]}

COMMAND_OUTPUT_with_script_file = """xyz@debian:~$ sed -f script old old2 > new
xyz@debian:~$"""

COMMAND_KWARGS_with_script_file = {
    "script_files": ["script"],
    "output_file": "new",
    "input_files": ["old", "old2"],
}

COMMAND_RESULT_with_script_file = {"RESULT": []}

COMMAND_OUTPUT_with_option = """xyz@debian:~$ sed -i -e 's/a/A/' old old2
xyz@debian:~$"""

COMMAND_KWARGS_with_option = {
    "options": "-i",
    "scripts": ["s/a/A/"],
    "input_files": ["old", "old2"],
}

COMMAND_RESULT_with_option = {"RESULT": []}
