# -*- coding: utf-8 -*-
"""
Exit command module.
"""

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2023, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'


from moler.cmd.commandchangingprompt import CommandChangingPrompt


class Exit(CommandChangingPrompt):
    def __init__(self, connection, prompt=None, expected_prompt='>', newline_chars=None, runner=None,
                 target_newline="\n", allowed_newline_after_prompt=False, start_command_immediately=True):
        """
        :param connection: connection to device.
        :param expected_prompt: prompt on device changed by this command.
        :param prompt: expected prompt sending by device after command execution. Maybe String or compiled re.
        :param newline_chars:  new line chars on device (a list).
        :param runner: runner to run command.
        :param target_newline: newline on device when command is finished and prompt is changed.
        :param start_command_immediately: set True to set command_started before execution, False otherwise
        """
        super(Exit, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner,
                                   expected_prompt=expected_prompt, target_newline=target_newline,
                                   allowed_newline_after_prompt=allowed_newline_after_prompt)
        self._cmd_output_started = start_command_immediately

    def build_command_string(self):
        """
        Returns a string with command.

        :return: String with the command.
        """
        cmd = "exit"
        return cmd


COMMAND_OUTPUT = """
amu012@belvedere07:~$ exit
bash-4.2:~ #"""

COMMAND_KWARGS = {
    "expected_prompt": r'bash-4.2'
}

COMMAND_RESULT = {}
