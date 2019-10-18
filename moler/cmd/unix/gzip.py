# -*- coding: utf-8 -*-
"""
Gzip command module.
"""

__author__ = 'Dawid Gwizdz'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'dawid.gwizdz@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re


class Gzip(GenericUnixCommand):
    def __init__(self, connection, file_name, compressed_file_name=None, options=None, overwrite=False,
                 prompt=None, newline_chars=None, runner=None):
        super(Gzip, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.file_name = file_name
        self.compressed_file_name = compressed_file_name
        self.options = options
        self.overwrite = overwrite
        self.ret_required = False

    def build_command_string(self):
        cmd = 'gzip'
        if self.options:
            cmd = '{} {}'.format(cmd, self.options)
        cmd = '{} {}'.format(cmd, self.file_name)
        if self.compressed_file_name:
            cmd = '{} -c > {}'.format(cmd, self.compressed_file_name)
        return cmd

    def on_new_line(self, line, is_full_line):
        try:
            self._asks_to_overwrite(line)
            self._command_failure(line)
        except ParsingDone:
            pass
        return super(Gzip, self).on_new_line(line, is_full_line)

    _re_overwrite = re.compile(r"gzip:\s+(?P<COMPRESSED_FILE_NAME>.*)\s+already exists")

    def _asks_to_overwrite(self, line):
        if self._regex_helper.search_compiled(self._re_overwrite, line):
            if self.overwrite:
                self.connection.sendline('y')
            else:
                self.connection.sendline('n')
                self.set_exception(
                    CommandFailure(
                        self, "ERROR: {} already exists".format(self._regex_helper.group("COMPRESSED_FILE_NAME"))))
            raise ParsingDone

    _re_error = re.compile(r"gzip:\s(?P<ERROR_MSG>.*)")

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(self._re_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR_MSG"))))
            raise ParsingDone


COMMAND_OUTPUT = """xyz@debian:~$ gzip afile
xyz@debian:~$"""
COMMAND_KWARGS = {'file_name': 'afile'}
COMMAND_RESULT = {}

COMMAND_OUTPUT_options = """xyz@debian:~$ gzip -kv afile 
afile:	-13.3% -- replaced with afile.gz
xyz@debian:~$"""
COMMAND_KWARGS_options = {'file_name': 'afile', 'options': '-kv'}
COMMAND_RESULT_options = {}

COMMAND_OUTPUT_overwrite = """xyz@debian:~$ gzip afile 
gzip: kompresja.gz already exists; do you wish to overwrite (y or n)? y
xyz@debian:~$"""
COMMAND_KWARGS_overwrite = {'file_name': 'afile', 'overwrite': True}
COMMAND_RESULT_overwrite = {}

COMMAND_OUTPUT_compressed_file_name = """xyz@debian:~$ gzip afile -c > compresssed_file.gz
xyz@debian:~$"""
COMMAND_KWARGS_compressed_file_name = {'file_name': 'afile', 'compressed_file_name': 'compressed_file.gz'}
COMMAND_RESULT_compressed_file_name = {}
