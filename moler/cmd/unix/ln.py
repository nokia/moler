# -*- coding: utf-8 -*-
"""
Ln command module.
"""
from moler import connection_observer

__author__ = 'Haili Guo'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'haili.guo@nokia-sbell.com'

import re

from moler.cmd.unix.genericunix import GenericUnix
from moler.cmd.converterhelper import ConverterHelper
from moler.exceptions import CommandFailure


class Ln(GenericUnix):
    _re_ln_line = re.compile(r'(ln\:.*File exists)')

    def __init__(self, connection, prompt=None, new_line_chars=None, options=None):
        super(Ln, self).__init__(connection, prompt, new_line_chars)
        self._converter_helper = ConverterHelper()
        # Parameters defined by calling the command
        self.options = options
        self.ret_required = False

    def build_command_string(self):
        cmd = "ln"
        if self.options:
            cmd = cmd + " " + self.options
        return cmd

    def on_new_line(self, line, is_full_line):
        if self._cmd_output_started and self._regex_helper.search_compiled(Ln._re_ln_line, line):
            self.set_exception(CommandFailure(self,"ERROR: {}".format(self._regex_helper.group(1))))
        return super(Ln, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT ="""
user@server:~> ln -s file1 file2
user@server:~>"""


COMMAND_RESULT = {

}


COMMAND_KWARGS = {"options": "-s file1 file2"}