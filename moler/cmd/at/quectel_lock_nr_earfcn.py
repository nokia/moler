# -*- coding: utf-8 -*-
"""
AT+QNWCFG="nr5g_earfcn_lock",(0..32),earfcn1:scs1:...:earfcnN:scsN

AT commands specification:
google for: Quectel RG50xQRM5xxQ (R11 release and later)
This is internal Quectel AT command
(always check against the latest vendor release notes)
"""

__author__ = 'Jakub Kochaniak'
__copyright__ = 'Copyright (C) 2023, Nokia'
__email__ = 'jakub.kochaniak@nokia.com'

import re

from moler.cmd.at.genericat import GenericAtCommand
from moler.exceptions import ParsingDone


class SetQuectelLockNrEarfcn(GenericAtCommand):
    """
    Command to lock NR EARFCN. Example output:

    AT+QNWCFG="nr5g_earfcn_lock",1,433970:15
    OK
    """
    def __init__(self, earfcn, scs, connection=None, prompt=None, newline_chars=None, runner=None):
        """
        Quectel UE lock one EARFCN.

        :param earfcn: EARFCN number
        :param scs: SCS number
        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt where we start from.
        :param newline_chars: Characters to split local lines - list.
        :param runner: Runner to run command.
        """
        super(SetQuectelLockNrEarfcn, self).__init__(connection, operation="execute", prompt=prompt,
                                                     newline_chars=newline_chars, runner=runner)
        self.earfcn = int(earfcn)
        self.scs = int(scs)

    def build_command_string(self):
        command_prefix = 'AT+QNWCFG='
        command_values = '"nr5g_earfcn_lock",1,{}:{}'.format(self.earfcn, self.scs) if self.earfcn > 0 \
            else '"nr5g_earfcn_lock",0'
        return command_prefix + command_values

    _re_status = re.compile(r'^\s*(?P<STATUS>OK|ERROR|NO CARRIER)\s*$')

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        OK

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_status(line)
            except ParsingDone:
                pass
        return super(SetQuectelLockNrEarfcn, self).on_new_line(line, is_full_line)

    def _parse_status(self, line):
        """
        Parse At command status:

        OK
        or
        ERROR
        """
        if self._regex_helper.match_compiled(self._re_status, line):
            ip = self._regex_helper.group("STATUS")
            self.current_ret["status"] = ip
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
AT+QNWCFG="nr5g_earfcn_lock",1,433970:15
OK
"""

COMMAND_KWARGS_ver_execute = {'earfcn': 433970, 'scs': 15}

COMMAND_RESULT_ver_execute = {'status': 'OK'}
