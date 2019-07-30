# -*- coding: utf-8 -*-
"""
Testing of ip_neigh command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


def test_ip_neigh_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.ip_neigh import IpNeigh
    cmd = IpNeigh(connection=buffer_connection.moler_connection, options="show")
    assert "ip neigh show" == cmd.command_string
