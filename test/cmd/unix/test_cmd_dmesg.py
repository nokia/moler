# -*- coding: utf-8 -*-
"""
Testing of dmesg command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


def test_dmesg_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.dmesg import Dmesg
    cmd = Dmesg(connection=buffer_connection.moler_connection, options="--color")
    assert "dmesg --color" == cmd.command_string
