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
    def __init__(self, connection, input_options=None, output_options=None, options=None, prompt=None,
                 newline_chars=None, runner=None):
        super(Socat, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.input_options = input_options
        self.output_options = output_options
        self.options = options
        self.current_ret['RESULT'] = list()
        self.current_ret['INFO'] = list()
        self.current_ret['FEATURES'] = dict()
        self.current_ret['FEATURES']['defined'] = dict()
        self.current_ret['FEATURES']['undefined'] = list()

    def build_command_string(self):
        cmd = 'socat'
        if self.options:
            cmd = cmd + ' ' + self.options
        if self.input_options:
            cmd = cmd + ' ' + self.input_options
        if self.output_options:
            cmd = cmd + ' ' + self.output_options
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_failure(line)
                self._remove_features(line)
                self._parse_info_msg(line)
                self._parse_info_dict_define(line)
                self._parse_info_dict_undefined(line)
                self._parse_output(line)
            except ParsingDone:
                pass
        return super(Socat, self).on_new_line(line, is_full_line)

    _re_error = re.compile(r'.* socat\[\d*\]\s[E|F]\s(?P<ERROR_MSG>.*)')

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Socat._re_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR_MSG"))))
            raise ParsingDone

    _re_features = re.compile(r"features:")

    def _remove_features(self, line):
        if self._regex_helper.search_compiled(Socat._re_features, line):
            raise ParsingDone

    _re_info = re.compile(r'.* socat\[\d*\]\s(?P<INFO_MSG>[NWID].*)')

    def _parse_info_msg(self, line):
        if self._regex_helper.search_compiled(Socat._re_info, line):
            info_msg = self._regex_helper.group("INFO_MSG")
            self.current_ret['INFO'].append(info_msg)
            raise ParsingDone

    _re_define = re.compile(r"#define\s+(?P<KEY>.*_.*)\s+(?P<VALUE>\d+)")

    def _parse_info_dict_define(self, line):
        if self._regex_helper.search_compiled(Socat._re_define, line):
            key = self._regex_helper.group("KEY")
            value = self._regex_helper.group("VALUE")
            row_dict = {key: value}
            self.current_ret['FEATURES']['defined'].update(row_dict)
            raise ParsingDone

    _re_undefined = re.compile(r"#undef\s+(?P<FEATURE>.*_.*)")

    def _parse_info_dict_undefined(self, line):
        if self._regex_helper.search_compiled(Socat._re_undefined, line):
            feature = self._regex_helper.group("FEATURE")
            self.current_ret['FEATURES']['undefined'].append(feature)
            raise ParsingDone

    def _parse_output(self, line):
        self.current_ret['RESULT'].append(line.strip())
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
    'RESULT': [],
    'INFO': ['N PTY is /dev/pts/2', 'N PTY is /dev/pts/4', 'N starting data transfer loop with FDs [5,5] and [7,7]'],
    'FEATURES': {'defined': {}, 'undefined': []}
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
    'RESULT': ['Mon Aug 20 10:37:14 CEST 2018'],
    'INFO': [],
    'FEATURES': {'defined': {}, 'undefined': []}
}


COMMAND_OUTPUT_both_types = """
xyz@debian:~$ socat -d - EXEC:'ssh -l userName server1.nixcraft.net.in',pty,setsid,ctty
2018/08/20 11:14:46 socat[31539] W open("/dev/tty", O_NOCTTY, 0640): No such device or address
ssh: Could not resolve hostname server1.nixcraft.net.in: Name or service not known
2018/08/20 11:14:46 socat[31538] W waitpid(): child 31539 exited with status 255
xyz@debian:~$"""

COMMAND_KWARGS_both_types = {
    'options': '-d',
    'input_options': '-',
    'output_options': "EXEC:'ssh -l userName server1.nixcraft.net.in',pty,setsid,ctty"
}

COMMAND_RESULT_both_types = {
    'RESULT': ['ssh: Could not resolve hostname server1.nixcraft.net.in: Name or service not known'],
    'INFO': ['W open("/dev/tty", O_NOCTTY, 0640): No such device or address',
             'W waitpid(): child 31539 exited with status 255'],
    'FEATURES': {'defined': {}, 'undefined': []}
}


COMMAND_OUTPUT_version = """
xyz@debian:~$ socat -V
socat by Gerhard Rieger - see www.dest-unreach.org
socat version 1.7.3.1 on Jul 14 2017 13:52:03
   running on Linux version #1 SMP Debian 4.9.88-1+deb9u1 (2018-05-07), release 4.9.0-6-amd64, machine x86_64
features:
  #define WITH_STDIO 1
  #define WITH_FDNUM 1
  #define WITH_FILE 1
  #define WITH_CREAT 1
  #define WITH_GOPEN 1
  #define WITH_TERMIOS 1
  #define WITH_PIPE 1
  #undef WITH_READLINE
  #define WITH_MSGLEVEL 0 /*debug*/
xyz@debian:~$"""

COMMAND_KWARGS_version = {
    'options': '-V'
}

COMMAND_RESULT_version = {
    'RESULT': ['socat by Gerhard Rieger - see www.dest-unreach.org', 'socat version 1.7.3.1 on Jul 14 2017 13:52:03',
               'running on Linux version #1 SMP Debian 4.9.88-1+deb9u1 (2018-05-07), release 4.9.0-6-amd64,'
               ' machine x86_64'],
    'INFO': [],
    'FEATURES': {'defined': {'WITH_CREAT': '1',
                             'WITH_FDNUM': '1',
                             'WITH_FILE': '1',
                             'WITH_GOPEN': '1',
                             'WITH_MSGLEVEL': '0',
                             'WITH_PIPE': '1',
                             'WITH_STDIO': '1',
                             'WITH_TERMIOS': '1'},
                 'undefined': ['WITH_READLINE']}
}
