# -*- coding: utf-8 -*-
"""
Which command module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Which(GenericUnixCommand):
    def __init__(self, connection, names, show_all=None, prompt=None, new_line_chars=None):
        super(Which, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        # Parameters defined by calling the command
        self.names = names
        self.show_all = show_all

        self._set_result_keys()

        # Internal variables
        self._result_set = False

    def build_command_string(self):
        cmd = "which"
        if self.show_all:
            cmd = cmd + " -a"
        for name in self.names:
            cmd = cmd + " {}".format(name)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse(line)
            except ParsingDone:
                pass
        elif not self.done() and not self._result_set:
            self.set_result({})
        return super(Which, self).on_new_line(line, is_full_line)

    def _parse(self, line):
        for name in self.names:
            _re_name = re.compile(r"(?P<NAME>.*%s.*)" % name, re.IGNORECASE)

            if self._regex_helper.search_compiled(_re_name, line):
                self.current_ret[name].append(self._regex_helper.group("NAME"))
                self._result_set = True
                raise ParsingDone

    def _set_result_keys(self):
        for name in self.names:
            if name and name.split(" \t\n\r\f\v"):
                self.current_ret[name] = list()


COMMAND_OUTPUT = """
xyz@debian:~$ which uname git
/bin/uname
/usr/bin/git
xyz@debian:~$"""

COMMAND_KWARGS = {
    'names': ['uname', 'git']
}

COMMAND_RESULT = {'uname': ['/bin/uname'], 'git': ['/usr/bin/git']}


COMMAND_OUTPUT_all = """
xyz@debian:~$ which -a git less
/usr/bin/git
/usr/bin/less
/bin/less
xyz@debian:~$"""

COMMAND_KWARGS_all = {
    'names': ['git', 'less'], 'show_all': True
}

COMMAND_RESULT_all = {'git': ['/usr/bin/git'], 'less': ['/usr/bin/less', '/bin/less']}


COMMAND_OUTPUT_no_result = """
xyz@debian:~$ which -a abc
xyz@debian:~$"""

COMMAND_KWARGS_no_result = {
    'names': ['abc'], 'show_all': True
}

COMMAND_RESULT_no_result = {}
