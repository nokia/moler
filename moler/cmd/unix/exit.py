# -*- coding: utf-8 -*-
"""
Exit command module.
"""

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'


from moler.cmd.commandchangingprompt import CommandChangingPrompt


class Exit(CommandChangingPrompt):
    def __init__(self, connection, prompt=None, expected_prompt='>', newline_chars=None, runner=None,
                 target_newline="\n"):
        """
        :param connection:
        :param prompt: Prompt of the starting shell
        :param expected_prompt: Prompt of the target shell reached after exit command
        :param newline_chars:
        """
        super(Exit, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner,
                                   expected_prompt=expected_prompt, target_newline=target_newline)

    def build_command_string(self):
        cmd = "exit"
        return cmd


COMMAND_OUTPUT = """
amu012@belvedere07:~$ exit
bash-4.2:~ #"""

COMMAND_KWARGS = {
    "expected_prompt": r'bash-4.2'
}

COMMAND_RESULT = {}
