# -*- coding: utf-8 -*-
"""
Socat command module.
"""

__author__ = 'Adrianna Pienkowska'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re


class Socat(GenericUnixCommand):
    def __init__(self, connection, input_options, output_options, options=None):
        super(Socat, self).__init__(connection=connection)
        self.input_options = input_options
        self.output_options = output_options
        self.options = options
        self.current_ret['RESULT'] = list()
        self.current_ret['RESULT'].extend([{'OUTPUT': list(), 'INFO': list()}])

    def build_command_string(self):
        cmd = 'socat'
        if self.options:
            cmd = cmd+' '+self.options
        if self.input_options:
            cmd = cmd+' '+self.input_options
        if self.output_options:
            cmd = cmd+' '+self.output_options
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_failure(line)
                self._parse_info_msg(line)
                self._parse_output(line)
            except ParsingDone:
                pass
        return super(Socat, self).on_new_line(line, is_full_line)

    _re_error = re.compile(r'.* socat\[\d*\]\s[E|F]\s(?P<ERROR_MSG>.*)')

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Socat._re_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR_MSG"))))
            raise ParsingDone

    _re_info = re.compile(r'.* socat\[\d*\]\s[N|W|I|D]\s(?P<INFO_MSG>.*)')

    def _parse_info_msg(self, line):
        if self._regex_helper.search_compiled(Socat._re_info, line):
            info_msg = self._regex_helper.group("INFO_MSG")
            self.current_ret['RESULT'][0]['INFO'].append(info_msg)
            raise ParsingDone

    def _parse_output(self, line):
        self.current_ret['RESULT'][0]['OUTPUT'].append(line)
        raise ParsingDone


COMMAND_OUTPUT_info_output = """
xyz@debian:~$ socat -d -d pty,raw,echo=0,b9600 pty,raw,echo=0,b9600
2016/01/16 12:57:51 socat[18255] N PTY is /dev/pts/2
2016/01/16 12:57:51 socat[18255] N PTY is /dev/pts/4
2016/01/16 12:57:51 socat[18255] N starting data transfer loop with FDs [5,5] and [7,7]
xyz@debian:~$"""

COMMAND_KWARGS_info_output = {
    'options': '-d -d',
    'input_options': 'pty,raw,echo=0,b9600',
    'output_options': 'pty,raw,echo=0,b9600'
}

COMMAND_RESULT_info_output = {
    'RESULT': [{'OUTPUT': [], 'INFO': ['PTY is /dev/pts/2', 'PTY is /dev/pts/4',
               'starting data transfer loop with FDs [5,5] and [7,7]']}]
}


COMMAND_OUTPUT_basic_output = """
xyz@debian:~$ socat SYSTEM:date -
Mon Aug 20 10:37:14 CEST 2018
xyz@debian:~$"""

COMMAND_KWARGS_basic_output = {
    'input_options': 'SYSTEM:date',
    'output_options': '-'
}

COMMAND_RESULT_basic_output = {
    'RESULT': [{'OUTPUT': ['Mon Aug 20 10:37:14 CEST 2018'], 'INFO': []}]
}