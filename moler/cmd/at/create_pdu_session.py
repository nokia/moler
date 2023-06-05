# -*- coding: utf-8 -*-
"""
AT$QCRMCALL=1,1

AT commands specification:
google for: 3gpp specification 27.007
(always check against the latest version of standard)
"""

__author__ = 'Adam Klekowski'
__copyright__ = 'Copyright (C) 2023, Nokia'
__email__ = 'adam.klekowski@nokia.com'

import re

from moler.cmd.at.genericat import GenericAtCommand
from moler.exceptions import ParsingDone, CommandFailure


class CreatePduSession(GenericAtCommand):
    """
    Command to establish PDU session. Example output:

    AT$QCRMCALL=1,1
    OK
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of CreatePduSession class"""
        super(CreatePduSession, self).__init__(connection, operation='execute', prompt=prompt,
                                               newline_chars=newline_chars, runner=runner)

    def build_command_string(self):
        return "AT$QCRMCALL=1,1"

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None.
        """
        try:
            self._check_command_failure(line)
        except ParsingDone:
            pass
        super(CreatePduSession, self).on_new_line(line=line, is_full_line=is_full_line)

    _re_command_fail = re.compile("^NO CARRIER$", re.IGNORECASE)

    def _check_command_failure(self, line):
        """
        Checks if line has info about command failure.

        :param line: Line from device.
        :return: None
        :raise ParsingDone: if regex matches.
        """
        if self._regex_helper.search_compiled(self._re_command_fail, line):
            self.set_exception(CommandFailure(self, "Found error regex in line '{}'".format(line)))
            raise ParsingDone


# -----------------------------------------------------------------------------
# Following documentation is required for library CI.
# It is used to perform command self-test.
#
# Moreover, it documents what will be COMMAND_RESULT when command
# is run with COMMAND_KWARGS on COMMAND_OUTPUT data coming from connection.
#
# When you need to show parsing of multiple outputs just add suffixes:
# COMMAND_OUTPUT_suffix
# COMMAND_KWARGS_suffix
# COMMAND_RESULT_suffix
# -----------------------------------------------------------------------------

COMMAND_OUTPUT_ver_execute = """
AT$QCRMCALL=1,1
OK
"""

COMMAND_KWARGS_ver_execute = {}

COMMAND_RESULT_ver_execute = {}
