# -*- coding: utf-8 -*-
"""
Sudo command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Sudo(GenericUnixCommand):

    def __init__(self, connection, sudo_password, cmd_object=None, cmd_class_name=None, cmd_params=None, prompt=None, newline_chars=None, runner=None):
        super(Sudo, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.sudo_password = sudo_password
        self.cmd_object = cmd_object
        self._sent_sudo_password = False
        self._sent_command_string = False
        if cmd_class_name:
            params = dict()
            if cmd_params is not None:
                params = cmd_params.copy()
            params["connection"] = connection
            params['prompt'] = prompt
            params["newline_chars"] = newline_chars
            #params["runner"] = runner
        if not self.cmd_object:
            self.set_exception(CommandFailure("Neither 'cmd_class_name' nor 'cmd_object' was provided to Sudo constructor. Please specific parameter."))

    def build_command_string(self):
        cmd = "sudo {}".format(self.cmd_object.command_string)
        return cmd

    def on_new_line(self, line, is_full_line):
        try:
            self._parse_sudo_password(line)
        except ParsingDone:
            pass
        super(Sudo, self).on_new_line(line, is_full_line)

    _re_sudo_password = re.compile(r"\[sudo\] password for.*:", re.I)

    def _parse_sudo_password(self, line):
        if re.search(Sudo._re_sudo_password, line):
            if not self._sent_sudo_password:
                self.connection.sendline(self.sudo_password)
                self._sent_sudo_password = True
            raise ParsingDone()
