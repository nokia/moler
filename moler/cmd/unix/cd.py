# -*- coding: utf-8 -*-
"""
cd command module.
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

from re import compile, escape, IGNORECASE

from moler.cmd.unix.genericunix import GenericUnixCommand


class Cd(GenericUnixCommand):

    def __init__(self, connection, path=None, prompt=None, newline_chars=None, runner=None):
        super(Cd, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        # Parameters defined by calling the command
        self.path = path

        # command parameters
        self.ret_required = False

    def build_command_string(self):
        cmd = "cd"
        if self.path:
            cmd = "{} {}".format(cmd, self.path)
        return cmd

    def on_new_line(self, line, is_full_line):
        if not is_full_line:
            return super(Cd, self).on_new_line(line, is_full_line)

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
