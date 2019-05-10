# -*- coding: utf-8 -*-
"""
Exit telnet command
"""

from moler.cmd.unix.exit_telnet import ExitTelnet as ExitTelnetUnix

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class ExitTelnet(ExitTelnetUnix):
    pass


COMMAND_OUTPUT = """
telnet> exit
moler_bash#"""

COMMAND_KWARGS = {
    "expected_prompt": r'^moler_bash#'
}

COMMAND_RESULT = {}
