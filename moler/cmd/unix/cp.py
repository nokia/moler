# -*- coding: utf-8 -*-
"""
Cp command module.
"""

__author__ = 'Julia Patacz, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'julia.patacz@nokia.com, marcin.usielski@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure


class Cp(GenericUnixCommand):
    def __init__(self, connection, src, dst, options=None, prompt=None, newline_chars=None, runner=None):
        super(Cp, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        self.src = src
        self.dst = dst
        self.options = options
        self.ret_required = False

        # self._reg_fail = compile(r'(cp\: cannot access)')

    def build_command_string(self):
        if self.options:
            cmd = "{} {} {} {}".format("cp", self.options, self.src, self.dst)
        else:
            cmd = "{} {} {}".format("cp", self.src, self.dst)
        return cmd

    def on_new_line(self, line, is_full_line):
        if self._cmd_output_started and self._regex_helper.search(r'(cp\: cannot access)', line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group(1))))
        return super(Cp, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT = """
user@server:~> cp uses.pl uses.pl.bak
user@server:~>"""

COMMAND_RESULT = {

}

COMMAND_KWARGS = {
    "src": "uses.pl",
    "dst": "uses.pl.bak",
}

COMMAND_OUTPUT_options = """
user@server:~$ cp -v src.txt dst.txt
'src.txt' -> 'dst.txt'
user@dserver:$"""

COMMAND_RESULT_options = {

}

COMMAND_KWARGS_options = {
    "src": "src.txt",
    "dst": "dst.txt",
    "options": "-v"
}
