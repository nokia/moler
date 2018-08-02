# -*- coding: utf-8 -*-
"""
Sed command module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Sed(GenericUnixCommand):

    def __init__(self, connection, input_files, prompt=None, new_line_chars=None, options=None, scripts=None,
                 script_files=None, output_file=None):
        super(Sed, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        # Parameters defined by calling the command
        self.options = options            # list of strings
        self.scripts = scripts            # list of strings
        self.script_files = script_files  # list of strings
        self.input_files = input_files    # list of strings
        self.output_file = output_file    # string

        self._is_input_file()
        self._is_script()

        # Other parameters
        self.current_ret['RESULT'] = list()
        self._result_set = False

    def build_command_string(self):
        cmd = "sed"
        if self.options:
            for option in self.options:
                cmd = cmd + " {}".format(option)
        if self.scripts:
            for script in self.scripts:
                cmd = cmd + " -e '{}'".format(script)
        if self.script_files:
            for file in self.script_files:
                cmd = cmd + " -f {}".format(file)
        if self.input_files:
            for in_file in self.input_files:
                cmd = cmd + " " + in_file
        if self.output_file:
            cmd = cmd + " > " + self.output_file
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_error(line)
                self._parse(line)
            except ParsingDone:
                pass
        elif not self.done() and not self._result_set:
            self.set_result({})
        return super(Sed, self).on_new_line(line, is_full_line)

    _re_command_error = re.compile(r"sed:\s(?P<ERROR>.*)", re.IGNORECASE)

    def _command_error(self, line):
        if self._regex_helper.search_compiled(Sed._re_command_error, line):
            self.set_exception(CommandFailure(self, "ERROR {}".format(self._regex_helper.group("ERROR"))))
            raise ParsingDone

    def _parse(self, line):
        self.current_ret['RESULT'].append(line)
        self._result_set = True
        raise ParsingDone

    def _is_input_file(self):
        is_empty = True
        for file in self.input_files:
            if file and file.strip(" \t\n\r\f\v"):
                is_empty = False
        if is_empty:
            self.set_exception(CommandFailure(self, "No input file given in: {}".format(self.input_files)))

    def _is_script(self):
        is_empty = True
        if self.script_files:
            for s_file in self.script_files:
                if s_file and s_file.strip(" \t\n\r\f\v"):
                    is_empty = False
        if self.scripts:
            for script in self.scripts:
                if script and script.strip(" \t\n\r\f\v"):
                    is_empty = False
        if is_empty:
            self.set_exception(CommandFailure(self, "No script given in: {} or {}".format(self.scripts,
                                                                                          self.script_files)))


COMMAND_OUTPUT = """xyz@debian:~$ sed -e 's/a/A/' old old2 > new
xyz@debian:~$"""

COMMAND_KWARGS = {
    'scripts': ['s/a/A/'], 'output_file': 'new', 'input_files': ['old', 'old2']
}

COMMAND_RESULT = {}


COMMAND_OUTPUT_to_stdout = """xyz@debian:~$ sed -e 's/a/A/' old old2
Aga
Ania
Andrzej
Antoni
jAblko
gruszkA
xyz@debian:~$"""

COMMAND_KWARGS_to_stdout = {
    'scripts': ['s/a/A/'], 'input_files': ['old', 'old2']
}

COMMAND_RESULT_to_stdout = {'RESULT': ['Aga', 'Ania', 'Andrzej', 'Antoni', 'jAblko', 'gruszkA']}
