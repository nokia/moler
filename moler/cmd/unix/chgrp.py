# -*- coding: utf-8 -*-
"""
Chgrp command module.
"""

__author__ = 'Adrianna Pienkowska'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re


class Chgrp(GenericUnixCommand):
    def __init__(self, connection, files, group, options=None, prompt=None, new_line_chars=None):
        super(Chgrp, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)
        self.options = options
        self.files = files
        self.group = group
        self.current_ret['RESULT'] = list()

    def build_command_string(self):
        cmd = "chgrp"
        if self.options:
            cmd = cmd + " " + self.options
        if self.group:
            cmd = cmd + " " + self.group
        if self.files:
            for file in self.files:
                cmd = cmd + " " + file
        else:
            pass
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse(line)
            except ParsingDone:
                pass
        elif not self.done():
            self.set_result({})
        return super(Chgrp, self).on_new_line(line, is_full_line)

    def _parse(self, line):
        self.current_ret['RESULT'].append(line)
        raise ParsingDone


COMMAND_OUTPUT_basic_test = """
xyz@debian:~$ chgrp test new
xyz@debian:~$"""

COMMAND_KWARGS_basic_test = {
    'group': "test",
    'files': ["new"]
}

COMMAND_RESULT_basic_test = {

}


COMMAND_OUTPUT_with_rfile = """
xyz@debian:~$ chgrp --reference=new new2
xyz@debian:~$"""

COMMAND_KWARGS_with_rfile = {
    'group': "--reference=new",
    'files': ["new2"]
}

COMMAND_RESULT_with_rfile = {

}
