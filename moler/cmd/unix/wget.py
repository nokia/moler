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

        self.options = options  # should contain URLs
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

    _re_command_error = list()
    _re_command_error.append(re.compile(r"(?P<ERROR>Connecting\sto\s.*\sfailed:.*)", re.I))
    _re_command_error.append(re.compile(r"wget:\s(?P<ERROR>.*)", re.I))

    def _command_error(self, line):
        for _re_error in Wget._re_command_error:
            if self._regex_helper.search_compiled(_re_error, line):
                self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR"))))
                raise ParsingDone

    _re_file_saved = re.compile(r"(?P<SAVED>\d\d\d\d-\d\d-\d\d\s\d\d:\d\d:\d\d\s\(\d+.\d+\s\w\w/s\)\s-\s.*)", re.I)

    def _parse_line(self, line):
        if self._regex_helper.search_compiled(Wget._re_file_saved, line):
            self.current_ret['RESULT'].append(self._regex_helper.group("SAVED"))
            raise ParsingDone


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
    'RESULT': ['2012-10-02 11:28:38 (58.9 KB/s) - wget-1.5.3.tar.gz']
}


COMMAND_OUTPUT_2 = """moler@debian:~$ wget -m http://users.student.com/lesson01/character.html
--2018-09-14 13:06:20--  http://users.student.com/lesson01/character.html
Connecting to 10.158.100.2:8080... connected.
Proxy request sent, awaiting response... 200 OK
Length: 3648 (3.6K) [text/html]
Saving to: ‘users.student.com/lesson01/character.html’

users.student.com/lesson01/character.htm 100%[=============================================>]   3.56K  --.-KB/s    in 0s      

2018-09-14 13:06:20 (210 MB/s) - ‘users.student.com/lesson01/character.html’ saved [3648/3648]

FINISHED --2018-09-14 13:06:20--
Total wall clock time: 0.2s
Downloaded: 1 files, 3.6K in 0s (210 MB/s)
moler@debian:~$"""

COMMAND_KWARGS_2 = {
    'options': '-m http://users.student.com/lesson01/character.html'
}

COMMAND_RESULT_2 = {
    'RESULT': ['2018-09-14 13:06:20 (210 MB/s) - ‘users.student.com/lesson01/character.html’ saved [3648/3648]']
}
