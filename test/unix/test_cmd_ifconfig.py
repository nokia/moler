# -*- coding: utf-8 -*-
"""
Testing of ifconfig command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


def test_ifconfig_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.ifconfig import Ifconfig
    ifconfig_cmd = Ifconfig(connection=buffer_connection.moler_connection, options="eth0")
    assert "ifconfig eth0" == ifconfig_cmd.command_string
