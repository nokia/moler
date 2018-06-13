# -*- coding: utf-8 -*-
"""
Testing of cat command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

from moler.cmd.unix.cat import Cat
from moler.exceptions import CommandFailure
import pytest


def test_cat_returns_proper_command_string(buffer_connection):
    cat_cmd = Cat(connection=buffer_connection.moler_connection, path="/home/ute/test")
    assert "cat /home/ute/test" == cat_cmd.command_string


def test_cat_raise_exception_wrong_path(buffer_connection):
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    cat_cmd = Cat(connection=buffer_connection.moler_connection, path="/home/test/test")
    with pytest.raises(CommandFailure, match=r'Command failed \'cat /home/test/test\' with ERROR: Is a directory'):
        cat_cmd()


@pytest.fixture
def command_output_and_expected_result():
    data = """
ute@debdev:~$ cat /home/test/test
cat: /home/ute/test: Is a directory
ute@debdev:~$
    """
    result = {

    }

    return data, result
