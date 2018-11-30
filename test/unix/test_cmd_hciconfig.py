# -*- coding: utf-8 -*-
"""
Testing of hciconfig command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


def test_hciconfig_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.hciconfig import Hciconfig
    cmd = Hciconfig(connection=buffer_connection.moler_connection, options="-a")
    assert "hciconfig -a" == cmd.command_string
