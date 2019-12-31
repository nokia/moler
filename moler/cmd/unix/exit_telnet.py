# -*- coding: utf-8 -*-
"""
Exit telnet command
"""
import re

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.cmd.commandchangingprompt import CommandChangingPrompt
from moler.exceptions import ParsingDone

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'


class ExitTelnet(CommandChangingPrompt):
    _re_telnet_prompt = re.compile(r"telnet>", re.IGNORECASE)

    def __init__(self, connection, newline_chars=None, prompt=None, runner=None, expected_prompt=r'moler_bash#',
                 set_timeout=None, set_prompt=None, target_newline="\n", allowed_newline_after_prompt=False,
                 prompt_after_login=None):
        """
        Class for exit telnet command.

        :param connection: moler connection to device, terminal when command is executed.
        :param prompt: prompt on start system (where command telnet starts).
        :param expected_prompt: prompt on server (where command telnet connects).
        :param set_timeout: Command to set timeout after telnet connects.
        :param set_prompt: Command to set prompt after telnet connects.
        :param newline_chars: characters to split lines.
        :param runner: Runner to run command.
        :param target_newline: newline chars on remote system where ssh connects.
        :param allowed_newline_after_prompt: If True then newline chars may occur after expected (target) prompt.
        :param prompt_after_login: prompt after login before send export PS1. If you do not change prompt exporting PS1
         then leave it None.
        """
        super(ExitTelnet, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                         runner=runner, expected_prompt=expected_prompt, set_timeout=set_timeout,
                                         set_prompt=set_prompt, target_newline=target_newline,
                                         allowed_newline_after_prompt=allowed_newline_after_prompt,
                                         prompt_after_login=prompt_after_login)

        self.target_newline = target_newline
        self.ret_required = False
        self._command_sent = False
        self._re_expected_prompt = CommandTextualGeneric._calculate_prompt(expected_prompt)
        self.newline_after_command_string = False

    def build_command_string(self):
        return "\x1d"

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        try:
            self._is_telnet_prompt(line)
            super(ExitTelnet, self).on_new_line(line=line, is_full_line=is_full_line)
        except ParsingDone:
            pass

    def _is_telnet_prompt(self, line):
        """
        Check that telnet prompt is in incoming line
        :param line: Line to process,
        :return: Nothing
        """
        if self._regex_helper.search_compiled(ExitTelnet._re_telnet_prompt, line) and (not self._command_sent):
            self.connection.sendline("q")
            self._command_sent = True

            raise ParsingDone

    def _detect_start_of_cmd_output(self, line, is_full_line):
        """
        :param line: line to check if echo of command is sent by device
        :param is_full_line:
        :return: Nothing
        """
        self._cmd_output_started = True


COMMAND_OUTPUT = """
toor4nsn@fzm-lsp-k2:~# \x1d
telnet> q
Connection closed.
moler_bash#"""

COMMAND_KWARGS = {}

COMMAND_RESULT = {}
