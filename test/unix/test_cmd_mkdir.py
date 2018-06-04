# -*- coding: utf-8 -*-
"""
Testing of mkdir command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'


def test_mkdir_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.mkdir import Mkdir
    mkdir_cmd = Mkdir(connection=buffer_connection.moler_connection, path="/home/ute/test")
    assert "mkdir /home/ute/test" == mkdir_cmd.command_string
