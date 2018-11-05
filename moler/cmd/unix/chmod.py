# -*- coding: utf-8 -*-
"""
chmod command module.
"""

__author__ = 'Yuping Sang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yuping.sang@nokia.com'
import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Chmod(GenericUnixCommand):
    def __init__(self, connection, permission, filename, options=None, prompt=None, newline_chars=None, runner=None):
        super(Chmod, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.permission = permission
        self.filename = filename
        self.options = options
        self.ret_required = False

    def build_command_string(self):
        if self.options:
            cmd = "{} {} {} {}".format("chmod", self.options, self.permission, self.filename)
        else:
            cmd = "{} {} {}".format("chmod", self.permission, self.filename)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_error(line)
            except ParsingDone:
                pass
        return super(Chmod, self).on_new_line(line, is_full_line)

    _reg_fail = re.compile(
        r'chmod: changing permissions of\s(?P<FILENAME>.*):\s(?P<ERROR>.*) '
        r'|chmod: cannot access\s(?P<FILENAME1>.*):  \s(?P<ERROR1>.*)'
        r'|chmod: WARNING: can\'t change|access\s(?P<FILENAME2>.*)')

    def _parse_error(self, line):
        if self._regex_helper.search(Chmod._reg_fail, line):
            self.set_exception(CommandFailure(self, "ERROR: {} or {}".format(self._regex_helper.group("ERROR"),
                                                                             self._regex_helper.group("ERROR1"))))
            raise ParsingDone


COMMAND_OUTPUT_ver_execute = """
ute@debdev:~$ chmod 777 test.txt
ute@debdev:~$ """


COMMAND_RESULT_ver_execute = {

}


COMMAND_KWARGS_ver_execute = {
    "permission": "777",
    "filename": "test.txt",
}

COMMAND_OUTPUT_option_execute = """
ute@debdev:~$ chmod -R 777 test
ute@debdev:~$ """


COMMAND_RESULT_option_execute = {

}


COMMAND_KWARGS_option_execute = {
    "options": "-R",
    "permission": "777",
    "filename": "test",
}
