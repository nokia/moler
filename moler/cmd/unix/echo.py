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
            """a = self.text.encode('unicode_escape')
            a = a.decode()"""
            cmd = "{} {}".format(cmd, repr(self.text))
        print(cmd)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                print("on_new_line")
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Echo, self).on_new_line(line, is_full_line)

    def _parse_line(self, line):
        self.current_ret["RESULT"].append(line)
        print("parse_line: " + line)
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


COMMAND_OUTPUT_n_option = """xyz@debian:~$ echo -n 'Hello world'
Hello worldxyz@debian:~$"""

COMMAND_KWARGS_n_option = {
    'options': '-n',
    'text': 'Hello world'
}

COMMAND_RESULT_n_option = {
    'RESULT': []
}


COMMAND_OUTPUT_e_option = """xyz@debian:~$ echo -e 'Hello \\rmy \\x08beautiful \\tcode!'
Hello \rmy \x08beautiful \tcode!
xyz@debian:~$"""

COMMAND_KWARGS_e_option = {
    'options': '-e',
    'text': 'Hello \rmy \bbeautiful \tcode!'
}

COMMAND_RESULT_e_option = {
    'RESULT': ['mybeautiful 	code!']
}


COMMAND_OUTPUT_e_option_new_line = """xyz@debian:~$ echo -e 'Hello \\nmy \\nbeautiful \\ncode!'
Hello \nmy \nbeautiful \ncode!
xyz@debian:~$"""

COMMAND_KWARGS_e_option_new_line = {
    'options': '-e',
    'text': 'Hello \nmy \nbeautiful \ncode!'
}

COMMAND_RESULT_e_option_new_line = {
    'RESULT': ['Hello ', 'my ', 'beautiful ', 'code!']
}
