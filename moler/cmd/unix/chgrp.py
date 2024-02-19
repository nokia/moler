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
    def __init__(self, connection, files, group, options=None, prompt=None, newline_chars=None, runner=None):
        super(Chgrp, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.options = options
        self.files = files
        self.group = group
        self.ret_required = False

    def build_command_string(self):
        cmd = "chgrp"
        if self.options:
            cmd = f"{cmd} {self.options}"
        if self.group:
            cmd = f"{cmd} {self.group}"
        if self.files:
            for file in self.files:
                cmd = f"{cmd} {file}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_failure(line)
            except ParsingDone:
                pass
        return super(Chgrp, self).on_new_line(line, is_full_line)

    _re_error = re.compile(r"chgrp:\s(?P<ERROR_MSG>.*)", re.IGNORECASE)

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Chgrp._re_error, line):
            self.set_exception(CommandFailure(self, f"ERROR: {self._regex_helper.group('ERROR_MSG')}"))
            raise ParsingDone


COMMAND_OUTPUT_basic_test = """
xyz@debian:~$ chgrp test new new2
xyz@debian:~$"""

COMMAND_KWARGS_basic_test = {
    'group': "test",
    'files': ["new", "new2"]
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
