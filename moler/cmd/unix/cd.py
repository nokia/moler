# -*- coding: utf-8 -*-
"""
cd command module.
"""
from re import compile, escape, IGNORECASE

from moler.cmd.unix.genericunix import GenericUnix

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'


class Cd(GenericUnix):
    # Compiled regexp
    _re_no_such_file_or_dir = compile(r"(.* No such file or directory)")

    def __init__(self, connection, path=None, prompt=None, new_line_chars=None):
        super(Cd, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        # Parameters defined by calling the command
        self.path = path

        # command parameters
        self.ret_required = False

        # regex

    def build_command_string(self):
        cmd = "cd"
        if self.path:
            cmd = cmd + " " + self.path
        return cmd

    def on_new_line(self, line, is_full_line):
        if not is_full_line:
            return super(Cd, self).on_new_line(line, is_full_line)
        if self._regex_helper.search_compiled(self._re_no_such_file_or_dir, line):
            self.set_exception(Exception("ERROR: {}".format(self._regex_helper.group(1))))

        return super(Cd, self).on_new_line(line, is_full_line)


# -----------------------------------------------------------------------------
# Following documentation is required for library CI.
# It is used to perform command self-test.
# Parameters:
# path is Optional.Path for Unix cd command
# -----------------------------------------------------------------------------

COMMAND_OUTPUT_ver_execute = """
host:~ # cd /home/ute/
host:/home/ute #
"""

COMMAND_KWARGS_ver_execute = {'path': '/home/ute'}

COMMAND_RESULT_ver_execute = {
}
