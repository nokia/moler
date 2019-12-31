# -*- coding: utf-8 -*-
"""
Testing of id command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


def test_id_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.ip_addr import IpAddr
    ip_addr_cmd = IpAddr(connection=buffer_connection.moler_connection, options="show")
    assert "ip addr show" == ip_addr_cmd.command_string
