# -*- coding: utf-8 -*-
"""
Wget command module.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re


class Wget(GenericUnixCommand):
    def __init__(self, connection, options, prompt=None, new_line_chars=None):
        super(Wget, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        self.options = options  # contains URLs
        self.current_ret['RESULT'] = list()

    def build_command_string(self):
        cmd = "wget " + self.options
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_error(line)
                self._parse_line(line)
            except ParsingDone:
                pass
        super(Wget, self).on_new_line(line, is_full_line)

    _re_connection_failure = re.compile(r"(?P<CONNECTION>Connecting\sto\s.*\sfailed:.*)", re.I)

    def _command_error(self, line):
        if self._regex_helper.search_compiled(Wget._re_connection_failure, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("CONNECTION"))))
            raise ParsingDone

    def _parse_line(self, line):
        self.current_ret['RESULT'].append(line)


COMMAND_OUTPUT = """moler@debian:~$ wget http://ftp.gnu.org/gnu/wget/wget-1.5.3.tar.gz
--2012-10-02 11:28:30--  http://ftp.gnu.org/gnu/wget/wget-1.5.3.tar.gz
Resolving ftp.gnu.org... 208.118.235.20, 2001:4830:134:3::b
Connecting to ftp.gnu.org|208.118.235.20|:80... connected.
HTTP request sent, awaiting response... 200 OK
Length: 446966 (436K) [application/x-gzip]
Saving to: wget-1.5.3.tar.gz
100%[===================================================================================>] 446,966     60.0K/s   in 7.4s
2012-10-02 11:28:38 (58.9 KB/s) - wget-1.5.3.tar.gz
moler@debian:~$"""

COMMAND_KWARGS = {
    'options': 'http://ftp.gnu.org/gnu/wget/wget-1.5.3.tar.gz'
}

COMMAND_RESULT = {
    'RESULT': ['--2012-10-02 11:28:30--  http://ftp.gnu.org/gnu/wget/wget-1.5.3.tar.gz',
               'Resolving ftp.gnu.org... 208.118.235.20, 2001:4830:134:3::b',
               'Connecting to ftp.gnu.org|208.118.235.20|:80... connected.',
               'HTTP request sent, awaiting response... 200 OK',
               'Length: 446966 (436K) [application/x-gzip]',
               'Saving to: wget-1.5.3.tar.gz',
               '100%[===================================================================================>] '
               '446,966     60.0K/s   in 7.4s',
               '2012-10-02 11:28:38 (58.9 KB/s) - wget-1.5.3.tar.gz']
}
