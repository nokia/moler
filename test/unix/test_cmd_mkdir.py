# -*- coding: utf-8 -*-
"""
Testing of mkdir command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

from moler.cmd.unix.mkdir import Mkdir
from moler.exceptions import CommandFailure
import pytest


def test_mkdir_returns_proper_command_string(buffer_connection):
    mkdir_cmd = Mkdir(connection=buffer_connection.moler_connection, path="/home/ute/test")
    assert "mkdir /home/ute/test" == mkdir_cmd.command_string


def test_mkdir_raise_exception_wrong_path(buffer_connection):
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    mkdir_cmd = Mkdir(connection=buffer_connection.moler_connection, path="/home/test/test")
    with pytest.raises(CommandFailure):
        mkdir_cmd()


@pytest.fixture
def command_output_and_expected_result():
    data = """
ute@debdev:~$ mkdir /home/test/test
mkdir: cannot create directory /home/test/test: No such file or directory
ute@debdev:~$
    """
    result = {

    }

    return data, result
