# -*- coding: utf-8 -*-
"""
Testing of tail command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

from moler.cmd.unix.tail import Tail
from moler.exceptions import CommandFailure
import pytest


def test_tail_returns_proper_command_string(buffer_connection):
    cmd = Tail(connection=buffer_connection.moler_connection, path="/home/ute/test", options="-n 10")
    assert "tail /home/ute/test -n 10" == cmd.command_string


def test_tail_raise_exception(buffer_connection):
    command_output = """
ute@debdev:~$ tail test.txt
tail: cannot open test.txt for reading: No such file or directory
ute@debdev:~$"""
    buffer_connection.remote_inject_response([command_output])
    cmd = Tail(connection=buffer_connection.moler_connection, path="test.txt")
    with pytest.raises(CommandFailure):
        cmd()
