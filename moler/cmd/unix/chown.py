# -*- coding: utf-8 -*-
"""
chown command module.
"""

__author__ = 'Yuping Sang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yuping.sang@nokia.com'
import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Chown(GenericUnixCommand):
    def __init__(self, connection, param, filename, options=None, prompt=None, newline_chars=None, runner=None):
        super(Chown, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.param = param
        self.filename = filename
        self.options = options
        self.ret_required = False

    def build_command_string(self):
        if self.options:
            cmd = "{} {} {} {}".format("chown", self.options, self.param, self.filename)
        else:
            cmd = "{} {} {}".format("chown", self.param, self.filename)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_error(line)
            except ParsingDone:
                pass
        return super(Chown, self).on_new_line(line, is_full_line)

    _reg_fail = re.compile(
        r'chown: missing operand after\s(?P<FILENAME>.*)'
        r'|chown: cannot access (?P<FILENAME1>.*):\s*(?P<ERROR>.*)'
        r'|chown: changing ownership of (?P<FILENAME2>.*):\s*(?P<ERROR1>.*)')

    def _parse_error(self, line):
        if self._regex_helper.search(Chown._reg_fail, line):
            self.set_exception(CommandFailure(self, "ERROR: {}or {}".format(self._regex_helper.group("ERROR"),
                                                                            self._regex_helper.group("ERROR1"))))
            raise ParsingDone


COMMAND_OUTPUT_change_user_execute = """
ute@debdev:~$ chown ute /rom/swconfig.txt
ute@debdev:~$
"""


COMMAND_RESULT_change_user_execute = {

}


COMMAND_KWARGS_change_user_execute = {
    "param": "ute",
    "filename": "/rom/swconfig.txt",
}

COMMAND_OUTPUT_change_user_and_group_execute = """
ute@debdev:~$ chown ute:ute /rom/swconfig1.txt
ute@debdev:~$ """


COMMAND_RESULT_change_user_and_group_execute = {

}


COMMAND_KWARGS_change_user_and_group_execute = {
    "param": "ute:ute",
    "filename": "/rom/swconfig1.txt",
}

COMMAND_OUTPUT_change_user_with_option_execute = """
ute@debdev:~$ chown -R ute /rom/swconfig
ute@debdev:~$ """


COMMAND_RESULT_change_user_with_option_execute = {

}


COMMAND_KWARGS_change_user_with_option_execute = {
    "options": "-R",
    "param": "ute",
    "filename": "/rom/swconfig",
}
