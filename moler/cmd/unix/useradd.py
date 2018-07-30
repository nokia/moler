# -*- coding: utf-8 -*-
"""
Useradd command module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Useradd(GenericUnixCommand):
    def __init__(self, connection, prompt=None, new_line_chars=None, options=None, defaults=None, user=None):
        super(Useradd, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        # Parameters defined by calling the command
        self.options = options
        self.defaults = defaults
        self.user = user

        # Internal variables
        self.current_ret['RESULT'] = list()
        self._result_set = False

    def build_command_string(self):
        cmd = "useradd"
        if self.defaults:
            cmd = cmd + " -D"
            if self.options:
                for d_option in self.options:
                    cmd = cmd + " {}".format(d_option)
        elif self.user:
            if self.options:
                for option in self.options:
                    cmd = cmd + " {}".format(option)
            cmd = cmd + " {}".format(self.user)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse(line)
            except ParsingDone:
                pass
        elif not self.done() and not self._result_set:
            self.set_result({})
        return super(Useradd, self).on_new_line(line, is_full_line)

    def _parse(self, line):
        self.current_ret['RESULT'].append(line)
        self._result_set = True
        raise ParsingDone

    _re_user_exists = re.compile(r"useradd:\suser\s.*\salready\sexists\s(?P<USER>.*)", re.I)
    _re_command_error_shows_help = re.compile(r"Usage:\suseradd\s\[options\]\sLOGIN\s(?P<HELP>.*)", re.I)
    _re_command_error = re.compile(r"useradd:\s.*\s(?P<ERROR>.*)", re.I)

    def _command_error(self, line):
        if self._regex_helper.search_compiled(Useradd._re_user_exists, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("USER"))))
            raise ParsingDone
        elif self._regex_helper.search_compiled(Useradd._re_command_error_shows_help, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("HELP"))))
            raise ParsingDone
        elif self._regex_helper.search_compiled(Useradd._re_command_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR"))))
            raise ParsingDone


"""
useradd: invalid user ID 'bylica'
Usage: useradd [options] LOGIN
useradd: user 'bylica' already exists
useradd: group '500' does not exist
useradd: UID 1001 is not unique
useradd: option requires an argument
"""
COMMAND_OUTPUT = """xyz@debian:~$ useradd -D
GROUP=100
HOME=/home
INACTIVE=-1
EXPIRE=
SHELL=/bin/sh
SKEL=/etc/skel
CREATE_MAIL_SPOOL=no
xyz@debian:~$"""

COMMAND_KWARGS = {
    'defaults': True
}

COMMAND_RESULT = {
    'RESULT': ['GROUP=100', 'HOME=/home', 'INACTIVE=-1', 'EXPIRE=', 'SHELL=/bin/sh', 'SKEL=/etc/skel',
               'CREATE_MAIL_SPOOL=no']
}
