# -*- coding: utf-8 -*-
"""
Gzip command module.
"""

__author__ = 'Dawid Gwizdz'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'dawid.gwizdz@nokia.com'

import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Gzip(GenericUnixCommand):
    def __init__(self, connection, file_name, compressed_file_name=None, options=None, overwrite=False,
                 prompt=None, newline_chars=None, runner=None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param file_name: Name of file to be compressed.
        :param compressed_file_name: Name of output compressed file if you want to specify other than default.
        :param options: Options of command gzip.
        :param overwrite: If true allows to overwrite existing file.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Gzip, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.file_name = file_name
        self.compressed_file_name = compressed_file_name
        self.options = options
        self.overwrite = overwrite
        self.answered_files = set()
        self.ret_required = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = 'gzip'
        if self.options:
            cmd = f'{cmd} {self.options}'
        cmd = f'{cmd} {self.file_name}'
        if self.compressed_file_name:
            cmd = f'{cmd} -c > {self.compressed_file_name}'
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        try:
            self._asks_to_overwrite(line)
            self._command_failure(line)
        except ParsingDone:
            pass
        return super(Gzip, self).on_new_line(line, is_full_line)

    _re_overwrite = re.compile(
        r"gzip:\s+(?P<COMPRESSED_FILE_NAME>.*)\s+already exists; do you wish to overwrite \(y or n\)?")

    def _asks_to_overwrite(self, line):
        """
        Parse line containing overwriting warning.
        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        if self._regex_helper.search_compiled(self._re_overwrite, line):
            compressed_file_name = self._regex_helper.group("COMPRESSED_FILE_NAME")
            if compressed_file_name not in self.answered_files:
                if self.overwrite:
                    self.connection.sendline('y')
                else:
                    self.connection.sendline('n')
                    self.set_exception(
                        CommandFailure(
                            self, f"ERROR: {compressed_file_name} already exists"))
                self.answered_files.add(compressed_file_name)
            raise ParsingDone

    _re_error = re.compile(r"gzip:\s(?P<ERROR_MSG>.*)")

    def _command_failure(self, line):
        """
        Parse line containing error.
        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        if self._regex_helper.search_compiled(self._re_error, line):
            self.set_exception(CommandFailure(self, f"ERROR: {self._regex_helper.group('ERROR_MSG')}"))
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
