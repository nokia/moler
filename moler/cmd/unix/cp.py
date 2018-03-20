# -*- coding: utf-8 -*-
"""
Cp command module.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com'


from moler.cmd.unix.genericunix import GenericUnix


class CpCommandFailure(Exception):
    pass


class Cp(GenericUnix):
    def __init__(self, connection, src, dst, options=None, prompt=None, new_line_chars=None):
        super(Cp, self).__init__(connection, prompt=prompt, new_line_chars=new_line_chars)

        self.src = src
        self.dst = dst
        self.options = options
        self.ret_required = False

        # self._reg_fail = compile(r'(cp\: cannot access)')

    def get_cmd(self, cmd=None):
        if not cmd:
            if self.options:
                cmd = "{} {} {} {}".format("cp", self.src, self.dst, self.options)
            else:
                cmd = "{} {} {}".format("cp", self.src, self.dst)
        return cmd

    def on_new_line(self, line, is_full_line):
        # if self._regex_helper.search_compiled(self._reg_fail, line):
        if self._cmd_matched and self._regex_helper.search(r'(cp\: cannot access)', line):
            self.set_exception(CpCommandFailure("ERROR: {}".format(self._regex_helper.group(1))))

        return super(Cp, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT = """
patacz@belvedere07:~> cp uses.pl uses.pl.bak
patacz@belvedere07:~>"""

COMMAND_RESULT = {

}

COMMAND_KWARGS = {
    "src": "uses.pl",
    "dst": "uses.pl.bak",
}
