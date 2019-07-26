# -*- coding: utf-8 -*-
"""
Testing of iptables command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


def test_iptables_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.iptables import Iptables
    cmd = Iptables(connection=buffer_connection.moler_connection, options="-nvxL", v6=True)
    assert "ip6tables -nvxL" == cmd.command_string
