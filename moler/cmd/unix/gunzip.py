# -*- coding: utf-8 -*-
"""
Gunzip command module.
"""

__author__ = 'Adrianna Pienkowska'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re


class Gunzip(GenericUnixCommand):
    def __init__(self, connection, archive_name, new_suffix=None, output_file_name=None, options=None, overwrite=False):
        super(Gunzip, self).__init__(connection=connection)
        self.archive_name = archive_name
        self.output_file_name = output_file_name
        self.options = options
        self.new_suffix = new_suffix
        self.overwrite = overwrite
        if self.options:
            self.ret_required = True
            self.current_ret['RESULT'] = list()
        else:
            self.ret_required = False

    def build_command_string(self):
        cmd = 'gunzip'
        if self.options:
            cmd = ' {} {}'.format(cmd, self.options)
        if self.new_suffix:
            cmd = ' {} -S {}'.format(cmd, self.new_suffix)
        if self.archive_name:
            for file in self.archive_name:
                cmd = ' {} {}'.format(cmd, file)
        if self.output_file_name:
            cmd = ' {} > {}'.format(cmd, self.output_file_name)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._asks_to_overwrite(line)
                self._command_failure(line)
                if self.ret_required:
                    self._parse_line(line)
            except ParsingDone:
                pass
        else:
            self._clean_result_if_empty()
        return super(Gunzip, self).on_new_line(line, is_full_line)

    _re_overwrite = re.compile(r"already exists;", re.IGNORECASE)

    def _asks_to_overwrite(self, line):
        if self._regex_helper.search_compiled(Gunzip._re_overwrite, line):
            if self.overwrite:
                self.connection.sendline('y')
                raise ParsingDone
            else:#to do jaki file
                self.set_exception(CommandFailure(self, "ERROR: file already exists and overwrite is set to False"))
                raise ParsingDone

    _re_error = re.compile(r"gzip:\s(?P<ERROR_MSG>.*)", re.IGNORECASE)

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Gunzip._re_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR_MSG"))))
            raise ParsingDone

    def _parse_line(self, line):
        self.current_ret['RESULT'].append(line)
        raise ParsingDone

    def _clean_result_if_empty(self):
        if self.ret_required and not self.current_ret['RESULT']:
            self.ret_required = False
            del self.current_ret['RESULT']


COMMAND_OUTPUT_without_options = """
xyz@debian:~$ gunzip new.gz
xyz@debian:~$"""

COMMAND_KWARGS_without_options = {
    'archive_name': ['new.gz']
}

COMMAND_RESULT_without_options = {}


COMMAND_OUTPUT_quiet_options = """
xyz@debian:~$ gunzip -c new.gz
xyz@debian:~$"""

COMMAND_KWARGS_quiet_options = {
    'archive_name': ['new.gz'],
    'options': '-c'
}

COMMAND_RESULT_quiet_options = {}


COMMAND_OUTPUT_loud_options = """
xyz@debian:~$ gunzip -v new.gz
new.gz:	 -7.7% -- replaced with new
xyz@debian:~$"""

COMMAND_KWARGS_loud_options = {
    'archive_name': ['new.gz'],
    'options': '-v'
}

COMMAND_RESULT_loud_options = {
    'RESULT': ['new.gz:\t -7.7% -- replaced with new']
}


COMMAND_OUTPUT_quiet_options_overwrite = """
xyz@debian:~$ gunzip new.gz
gzip: new5 already exists; do you wish to overwrite (y or n)?
xyz@debian:~$"""

COMMAND_KWARGS_quiet_options_overwrite = {
    'archive_name': ['new.gz'],
    'overwrite': 'True'
}

COMMAND_RESULT_quiet_options_overwrite = {
}


COMMAND_OUTPUT_loud_options_overwrite = """
xyz@debian:~$ gunzip -v new5.gz
gzip: new5 already exists; do you wish to overwrite (y or n)?
new5.gz:	  0.0% -- replaced with new5
xyz@debian:~$"""

COMMAND_KWARGS_loud_options_overwrite = {
    'archive_name': ['new5.gz'],
    'overwrite': 'True',
    'options': '-v'
}

COMMAND_RESULT_loud_options_overwrite = {
    'RESULT': ['new5.gz:\t  0.0% -- replaced with new5']
}