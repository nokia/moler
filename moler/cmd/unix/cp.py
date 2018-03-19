# -*- coding: utf-8 -*-
"""
Cp command module.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com'

from re import escape

from moler.cmd.unix.genericunix import GenericUnix


class CpCommandFailure(Exception):
    pass


class Cp(GenericUnix):
    def __init__(self, connection, src, dst, options=None):
        super(Cp, self).__init__(connection)

        self.src = src
        self.dst = dst
        self.options = options
        self.command_string = self.get_cmd()
        self.ret_required = False

        # self._reg_fail = compile(r'(cp\: cannot access)')

    def get_cmd(self, cmd="cp"):
        if self.options:
            cmd = "{} {} {} {}".format(cmd, self.src, self.dst, self.options)
        else:
            cmd = "{} {} {}".format(cmd, self.src, self.dst)
        self.command_string = cmd
        self._cmd_escaped = escape(cmd)
        return cmd

    def on_new_line(self, line):
        # if self._regex_helper.search_compiled(self._reg_fail, line):
        if self._cmd_matched and self._regex_helper.search(r'(cp\: cannot access)', line):
            self.set_exception(CpCommandFailure("ERROR: {}".format(self._regex_helper.group(1))))

        return super(Cp, self).on_new_line(line)

# co jesli komenda nic nie zwraca?!
