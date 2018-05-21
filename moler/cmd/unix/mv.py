# -*- coding: utf-8 -*-
"""
Mv command module.
"""

__author__ = 'Maciej Malczyk'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'maciej.malczyk@nokia.com'
import re
from moler.cmd.unix.genericunix import GenericUnix
from moler.exceptions import CommandFailure


class Mv(GenericUnix):
    _reg_fail_permission = re.compile(r'(mv: cannot (re)?move .*?: Permission denied)')
    _reg_fail_no_file = re.compile(r'(mv: cannot stat .*?: No such file or directory)')
    _reg_fail_crate_file = re.compile(r'(mv: cannot create regular file .*?: Permission denied)')
    _reg_fail_the_same = re.compile(r'(mv: .*? are the same file)')

    def __init__(self, connection, src, dst, options=None, prompt=None, new_line_chars=None):
        super(Mv, self).__init__(connection, prompt=prompt, new_line_chars=new_line_chars)

        self.src = src
        self.dst = dst
        self.options = options
        self.ret_required = False

    def build_command_string(self):
        return "{} {} {} {}".format("mv", self.src, self.dst, self.options) if self.options else "{} {} {}" \
            .format("mv", self.src, self.dst)

    def on_new_line(self, line, is_full_line):
        if self._cmd_output_started:
            if self._regex_helper.search(Mv._reg_fail_permission, line) or \
                    self._regex_helper.search(Mv._reg_fail_no_file, line) or \
                    self._regex_helper.search(Mv._reg_fail_the_same, line) or \
                    self._regex_helper.search(Mv._reg_fail_crate_file, line):
                self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group(1))))

        return super(Mv, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT_NO_FLAGS = """
ute@debdev:~$ mv moving_test.txt moving_tested.txt
ute@debdev:~$"""

COMMAND_RESULT_NO_FLAGS = {

}

COMMAND_KWARGS_NO_FLAGS = {
    "src": "moving_test.txt",
    "dst": "moving_tested.txt",
}

COMMAND_OUTPUT_WITH_FLAGS = """
ute@debdev:~$ mv moving_test moving_tested -f
ute@debdev:~$"""

COMMAND_RESULT_WITH_FLAGS = {}

COMMAND_KWARGS_WITH_FLAGS = {
    "src": "moving_test",
    "dst": "moving_tested",
    "options": "-f"
}
