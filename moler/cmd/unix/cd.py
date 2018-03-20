# -*- coding: utf-8 -*-
"""
cd command module.
"""
from re import compile, escape, IGNORECASE

from moler.cmd.unix.genericunix import GenericUnix

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'


class CdNoSuchFileOrDirectory(Exception):
    pass


class Cd(GenericUnix):
    def __init__(self, connection, path=None):
        super(Cd, self).__init__(connection)

        # Parameters defined by calling the command
        self.path = path

        # command parameters
        self.ret_required = False

        # regex
        self._reg_no_such_file_or_dir = compile(r"(.* No such file or directory)")

    def get_cmd(self, cmd="cd"):
        if self.path:
            cmd = cmd + " " + self.path
        return cmd

    def on_new_line(self, line):
        if self._cmd_matched and self._regex_helper.search_compiled(self._reg_no_such_file_or_dir, line):
            self.set_exception(CdNoSuchFileOrDirectory("ERROR: {}".format(self._regex_helper.group(1))))

        return super(Cd, self).on_new_line(line)


# -----------------------------------------------------------------------------
# Following documentation is required for library CI.
# It is used to perform command self-test.
#
# Moreover, it documents what will be COMMAND_RESULT when command
# is run with COMMAND_KWARGS on COMMAND_OUTPUT data coming from connection.
#
# When you need to show parsing of multiple outputs just add suffixes:
# COMMAND_OUTPUT_suffix
# COMMAND_KWARGS_suffix
# COMMAND_RESULT_suffix
# -----------------------------------------------------------------------------

COMMAND_OUTPUT_ver_execute = """
fzm-tdd-1:~ # cd /home/ute/
fzm-tdd-1:/home/ute #
"""

COMMAND_KWARGS_ver_execute = {'path': '/home/ute'}

COMMAND_RESULT_ver_execute = {
}
