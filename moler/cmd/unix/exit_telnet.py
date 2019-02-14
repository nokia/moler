# -*- coding: utf-8 -*-
"""
Exit telnet command
"""
import re

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'


class ExitTelnet(GenericUnixCommand):
    _re_telnet_prompt = re.compile(r"telnet>", re.IGNORECASE)

    def __init__(self, connection, prompt=None, newline_chars=None, expected_prompt=r'moler_bash#', runner=None,
                 target_newline="\n"):
        """
        :param connection:
        :param prompt: Prompt of the starting shell
        :param expected_prompt: Prompt of the target shell reached after quit command
        :param newline_chars:
        """
        super(ExitTelnet, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                         runner=runner)
        self.target_newline = target_newline
        self.ret_required = False
        self._command_sent = False
        self._re_expected_prompt = CommandTextualGeneric._calculate_prompt(expected_prompt)

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
            self._is_target_prompt(line)
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

    def _is_target_prompt(self, line):
        """
        Check that telnet prompt is in incoming line
        :param line: Line to process,
        :return: Nothing
        """
        if self._regex_helper.search_compiled(self._re_expected_prompt, line):
            if not self.done():
                self.set_result({})
                raise ParsingDone

    def _detect_start_of_cmd_output(self, line):
        """
        :param line: line to check if echo of command is sent by device
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
