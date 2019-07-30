# -*- coding: utf-8 -*-
"""
Testing of md5sum command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

from moler.cmd.unix.md5sum import Md5sum


def test_md5sum_returns_proper_command_string(buffer_connection):
    cmd = Md5sum(connection=buffer_connection.moler_connection, path="/home/ute/test", options="-b")
    assert "md5sum /home/ute/test -b" == cmd.command_string
