# -*- coding: utf-8 -*-
"""
Logout command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.cmd.unix.exit import Exit


class Logout(Exit):

    def build_command_string(self):
        return "logout"


COMMAND_OUTPUT = """
user@bhost:~$ logout
moler_bash#"""

COMMAND_KWARGS = {
    "expected_prompt": r'moler_bash#'
}

COMMAND_RESULT = {}
