# -*- coding: utf-8 -*-
"""
Hexdump command test module.
"""

__author__ = 'Agnieszka Bylica, Adrianna Pienkowska'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, adrianna.pienkowska@nokia,com'

import pytest
from moler.cmd.unix.hexdump import Hexdump
from moler.exceptions import CommandFailure

def test_hexdump_returns_proper_command_string(buffer_connection):
    hexdump_cmd = Hexdump(buffer_connection, files=["old"])
    assert "hexdump old" == hexdump_cmd.command_string


def test_hexdump_catches_empty_files_list(buffer_connection):
    hexdump_cmd = Hexdump(connection=buffer_connection.moler_connection, files=[" ", "  "])
    with pytest.raises(CommandFailure):
        hexdump_cmd()
