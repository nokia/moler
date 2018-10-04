# -*- coding: utf-8 -*-
"""
Which command module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Which(GenericUnixCommand):
    def __init__(self, connection, names, show_all=None, prompt=None, new_line_chars=None, runner=None):
        super(Which, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars, runner=runner)

        # Parameters defined by calling the command
        self.names = names
        self.show_all = show_all

        # Internal variables
        self._compiled_regex = []
        self._result_set = False
        self._set_result()

    def build_command_string(self):
        cmd = "which"
        if self.show_all:
            cmd = "{} {}".format(cmd, '-a')
        for name in self.names:
            cmd = "{} {}".format(cmd, name)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Which, self).on_new_line(line, is_full_line)

    def _parse_line(self, line):
        if not self._compiled_regex:
            self._compile_regex()
        for regex in self._compiled_regex:
            if self._regex_helper.search_compiled(regex[1], line):
                self.current_ret[regex[0]].append(self._regex_helper.group("NAME"))
                raise ParsingDone

    def _compile_regex(self):
        for name in self.names:
            _re_name = re.compile(r"(?P<NAME>.*{}.*)".format(name), re.IGNORECASE)
            self._compiled_regex.append((name, _re_name))

    def _set_result(self):
        if not self._result_set:
            for name in self.names:
                if not name:
                    self.set_exception(CommandFailure(self, "ERROR: name is empty"))
                else:
                    self.current_ret[name] = list()
            self._result_set = True


COMMAND_OUTPUT = """
xyz@debian:~$ which uname git
/bin/uname
/usr/bin/git
xyz@debian:~$"""

COMMAND_KWARGS = {
    'names': ['uname', 'git']
}

COMMAND_RESULT = {
    'uname': ['/bin/uname'],
    'git': ['/usr/bin/git']
}


COMMAND_OUTPUT_all = """
xyz@debian:~$ which -a git less
/usr/bin/git
/usr/bin/less
/bin/less
xyz@debian:~$"""

COMMAND_KWARGS_all = {
    'names': ['git', 'less'],
    'show_all': True
}

COMMAND_RESULT_all = {
    'git': ['/usr/bin/git'],
    'less': ['/usr/bin/less', '/bin/less']
}


COMMAND_OUTPUT_no_result = """
xyz@debian:~$ which -a abc
xyz@debian:~$"""

COMMAND_KWARGS_no_result = {
    'names': ['abc'],
    'show_all': True
}

COMMAND_RESULT_no_result = {
    'abc': []
}
