# -*- coding: utf-8 -*-
"""
Quit command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from moler.cmd.commandchangingprompt import CommandChangingPrompt


class Quit(CommandChangingPrompt):
    def __init__(self, connection, prompt=None, expected_prompt='moler_bash#', newline_chars=None, runner=None,
                 target_newline="\n", allowed_newline_after_prompt=False):
        """
        :param connection: connection to device.
        :param expected_prompt: prompt on device changed by this command.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        :param target_newline: newline on device when command is finished and prompt is changed.
        """
        super(Quit, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner,
                                   expected_prompt=expected_prompt, target_newline=target_newline,
                                   allowed_newline_after_prompt=allowed_newline_after_prompt)

    def build_command_string(self):
        """
        Returns a string with command.

        :return: String with the command.
        """
        cmd = "quit"
        return cmd


COMMAND_OUTPUT = """quit

Goodbye!
Connection closed by foreign host.
moler_bash#"""

COMMAND_KWARGS = {
    "expected_prompt": r'moler_bash#'
}

COMMAND_RESULT = {}
