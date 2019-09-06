# -*- coding: utf-8 -*-
"""
Echo command module.
"""
__author__ = 'Agnieszka Bylica, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, marcin.usielski@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Echo(GenericUnixCommand):
    def __init__(self, connection, options=None, text=None, write_mode=">", output_file=None, prompt=None,
                 newline_chars=None, runner=None, text_in_quotation=True):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param options: Options of command echo
        :param text: Text to echo
        :param write_mode: mode of write: '>' for truncate or '>>' for append
        :param output_file: path to file to write to
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        :param text_in_quotation: Set True if you need single quotation mark (') for parameter text, False if don't.
        """
        super(Echo, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        self.options = options
        self.text = text
        self.write_mode = write_mode
        self.output_file = output_file
        self.text_in_quotation = text_in_quotation

        self.current_ret['RESULT'] = list()

    def build_command_string(self):
        """
        :return: String representation of command to send over connection to device.
        """
        cmd = "echo"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        if self.text:
            if self.text_in_quotation:
                cmd = "{} {!r}".format(cmd, self.text)
            else:
                cmd = "{} {}".format(cmd, self.text)
        if self.output_file:
            cmd = "{} {} {}".format(cmd, self.write_mode, self.output_file)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        if is_full_line:
            try:
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Echo, self).on_new_line(line, is_full_line)

    def _parse_line(self, line):
        """
        :param line: string to append to RESULT
        :return: Nothing but raises ParsingDone
        """
        self.current_ret["RESULT"].append(line)
        raise ParsingDone


COMMAND_OUTPUT = """xyz@debian:~$ echo

xyz@debian:~$"""

COMMAND_KWARGS = {}

COMMAND_RESULT = {
    'RESULT': ['']
}


COMMAND_OUTPUT_variable = """xyz@debian:~$ echo $TERM
xterm
xyz@debian:~$"""

COMMAND_KWARGS_variable = {
    'text': '$TERM',
    'text_in_quotation': False
}

COMMAND_RESULT_variable = {
    'RESULT': ['xterm']
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


COMMAND_OUTPUT_e_option = """xyz@debian:~$ echo -e 'Hello \\rmy \\x08beautiful \\tdog!'
Hello \rmy \x08beautiful \tdog!
xyz@debian:~$"""

COMMAND_KWARGS_e_option = {
    'options': '-e',
    'text': 'Hello \rmy \bbeautiful \tdog!'
}

COMMAND_RESULT_e_option = {
    'RESULT': ['Hello ', 'my \x08beautiful \tdog!']
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
