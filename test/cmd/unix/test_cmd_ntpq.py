# -*- coding: utf-8 -*-
"""
Testing of ntpq command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


def test_ntpq_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.ntpq import Ntpq
    ntpq_cmd = Ntpq(connection=buffer_connection.moler_connection, options="-p")
    assert "ntpq -p" == ntpq_cmd.command_string
