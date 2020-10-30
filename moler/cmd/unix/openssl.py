# -*- coding: utf-8 -*-
"""
openssl module.
"""

__author__ = 'Marcin Szlapa'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.szlapa@nokia.com'

from moler.cmd.unix.su import Su


class Openssl(Su):
    """Command openssl."""

    def __init__(self, connection, prompt=None, expected_prompt=r'OpenSSL>',
                 newline_chars=None, runner=None, target_newline="\n", cmd_object=None,
                 cmd_class_name=None, cmd_params=None):
        """
        Command openssl.

        :param connection:.
        :param prompt: Prompt of the starting shell
        :param expected_prompt: Prompt of the target shell reached after exit command
        :param newline_chars:

        """
        if cmd_class_name or cmd_object:
            expected_prompt = None
        super(Openssl, self).__init__(connection=connection, prompt=prompt, expected_prompt=expected_prompt,
                                      newline_chars=newline_chars, runner=runner, target_newline=target_newline,
                                      cmd_object=cmd_object, cmd_class_name=cmd_class_name, cmd_params=cmd_params)

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        self._build_command_object()
        cmd = "openssl"
        if self.cmd_object:
            cmd = "{} -c \"{}\"".format(cmd, self.cmd_object.command_string)
        return cmd


COMMAND_OUTPUT = """
OpenSSL>"""

COMMAND_KWARGS = {
    "expected_prompt": r'OpenSSL>'
}

COMMAND_RESULT = {}

