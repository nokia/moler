# -*- coding: utf-8 -*-
"""
Userdel command module.
"""

__author__ = 'Agnieszka Bylica, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, marcin.usielski@nokia.com'


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Userdel(GenericUnixCommand):
    def __init__(self, connection, prompt=None, newline_chars=None, runner=None, options=None, user=None):
        super(Userdel, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                      runner=runner)

        self.options = options
        self.user = user

        self.current_ret['RESULT'] = list()

    def build_command_string(self):
        cmd = "userdel"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        if self.user:
            cmd = "{} {}".format(cmd, self.user)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_line_with_force_option(line)
                self._command_error(line)
            except ParsingDone:
                pass
        return super(Userdel, self).on_new_line(line, is_full_line)

    _re_command_error = re.compile(r"userdel:\s(?P<ERROR>.*)", re.IGNORECASE)
    _re_wrong_syntax = re.compile(r"Usage:\s(?P<HELP_MSG>.*)", re.IGNORECASE)

    def _command_error(self, line):
        if self._regex_helper.search_compiled(Userdel._re_command_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR"))))
            raise ParsingDone
        if self._regex_helper.search_compiled(Userdel._re_wrong_syntax, line):
            self.set_exception(CommandFailure(self, "ERROR: wrong syntax, should be: {}".format(
                self._regex_helper.group("HELP_MSG"))))
            raise ParsingDone

    _re_command_error_user_used = re.compile(r"userdel:\suser\s(?P<USER>.*)\sis\scurrently\sused\sby\sprocess"
                                             r"\s(?P<PROCESS>.*)", re.IGNORECASE)

    def _parse_line_with_force_option(self, line):
        if self.options:
            if self.options.find('-f') or self.options.find('--force'):
                if self._regex_helper.search_compiled(Userdel._re_command_error_user_used, line):
                    self.current_ret['RESULT'].append("User {} currently used by process {} was deleted".format(
                        self._regex_helper.group("USER"), self._regex_helper.group("PROCESS")))
                    raise ParsingDone


COMMAND_OUTPUT = """xyz@debian:~$ userdel tmp_user
xyz@debian:~$"""

COMMAND_KWARGS = {
    'user': 'tmp_user'
}

COMMAND_RESULT = {
    'RESULT': []
}


COMMAND_OUTPUT_with_option = """xyz@debian:~$ userdel --force tmp_user
xyz@debian:~$"""

COMMAND_KWARGS_with_option = {
    'user': 'tmp_user',
    'options': '--force'
}

COMMAND_RESULT_with_option = {
    'RESULT': []
}


COMMAND_OUTPUT_with_force_option = """xyz@debian:~$ userdel --force tmp_user2
userdel: user tmp_user2 is currently used by process 10274
xyz@debian:~$"""

COMMAND_KWARGS_with_force_option = {
    'user': 'tmp_user2',
    'options': '--force'
}

COMMAND_RESULT_with_force_option = {
    'RESULT': ['User tmp_user2 currently used by process 10274 was deleted']
}
