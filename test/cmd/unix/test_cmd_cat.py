# -*- coding: utf-8 -*-
"""
Testing of cat command.
"""
__author__ = 'Sylwester Golonka, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'sylwester.golonka@nokia.com, marcin.usielski@nokia.com'

from moler.cmd.unix.cat import Cat
from moler.exceptions import CommandFailure
import pytest


def test_cat_returns_proper_command_string(buffer_connection):
    cat_cmd = Cat(connection=buffer_connection.moler_connection, path="/home/ute/test")
    assert "cat /home/ute/test" == cat_cmd.command_string


def test_cat_raise_exception_wrong_path(buffer_connection, command_output):
    buffer_connection.remote_inject_response([command_output])
    cat_cmd = Cat(connection=buffer_connection.moler_connection, path="/home/test/test")
    cat_cmd()


def test_cat_raise_exception_wrong_path_exception(buffer_connection, command_output_exception):
    command_output = command_output_exception
    buffer_connection.remote_inject_response([command_output])
    cat_cmd = Cat(connection=buffer_connection.moler_connection, path="/home/test/test")
    with pytest.raises(CommandFailure):
        cat_cmd()


@pytest.fixture
def command_output():
    data = """
ute@debdev:~$ cat /home/test/test
cat: /home/ute/test: Is a directory
f6 FCT-E019-0-SmaLite \ufffd\ufffd\x7f \ufffd\ufffd\ufffd}"\ufffd\x02\ufffd?\ufffd\ufffd\ufffd\x08\ufffd\x05o\x1c
ute@debdev:~$"""
    return data


@pytest.fixture
def command_output_exception():
    data = """
ute@debdev:~$ cat /home/test/test
cat: /home/ute/test: Is a directory
ute@debdev:~$"""
    return data
