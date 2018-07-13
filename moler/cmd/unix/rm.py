# -*- coding: utf-8 -*-
"""
Rm command module.
"""

__author__ = 'Bartosz Odziomek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'bartosz.odziomek@nokia.com'

from moler.cmd.unix.genericunix import GenericUnix
from moler.exceptions import ParsingDone


class Rm(GenericUnix):
    def __init__(self, connection, file, options=None, prompt=None, new_line_chars=None):
        super(Rm, self).__init__(connection)

        self.file = file
        self.options = options
        self.ret_required = False

    def build_command_string(self):
        cmd = "{} {}".format('rm', self.file)
        if self.options:
            cmd = "{} {} {}".format('rm', self.options, self.file)

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
