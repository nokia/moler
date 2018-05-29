# -*- coding: utf-8 -*-
"""
Rm command module.
"""

__author__ = 'Bartosz Odziomek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'bartosz.odziomek@nokia.com'


def test_rm_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.rm import Rm
    rm_cmd = Rm(connection=buffer_connection.moler_connection, file="test.txt")
    assert "rm test.txt" == rm_cmd.command_string

