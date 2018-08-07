# -*- coding: utf-8 -*-
"""
Echo command module.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Echo(GenericUnixCommand):
    def __init__(self, connection, options=None, text=None, prompt=None, new_line_chars=None):
        super(Echo, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        self.options = options
        self.text = text

        self.current_ret['RESULT'] = list()

    def build_command_string(self):
        cmd = "echo"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        if self.text:
            cmd = "{} '{}'".format(cmd, self.text)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Echo, self).on_new_line(line, is_full_line)

    def _parse_line(self, line):
        self.current_ret["RESULT"].append(line)
        raise ParsingDone


COMMAND_OUTPUT = """xyz@debian:~$ echo

xyz@debian:~$"""

COMMAND_KWARGS = {}

COMMAND_RESULT = {
    'RESULT': ['']
}


COMMAND_OUTPUT_text = """xyz@debian:~$ echo 'abc'
abc
xyz@debian:~$"""

COMMAND_KWARGS_text = {
    'text': 'abc'
}

COMMAND_RESULT_text = {
    'RESULT': ['abc']
}


COMMAND_OUTPUT_e_option = """xyz@debian:~$ echo -e 'Tecmint \nis \na \ncommunity \nof \nLinux \nNerds'
Tecmint 
is 
a 
community 
of 
Linux 
Nerds
xyz@debian:~$"""

COMMAND_KWARGS_e_option = {
    'options': '-e',
    'text': 'Tecmint \nis \na \ncommunity \nof \nLinux \nNerds'
}

COMMAND_RESULT_e_option = {
    'RESULT': ['Tecmint', 'is', 'a', 'community', 'of', 'Linux', 'Nerds']
}
