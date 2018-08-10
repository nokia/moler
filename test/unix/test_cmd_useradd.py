# -*- coding: utf-8 -*-
"""
Useradd test module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import pytest

from moler.exceptions import CommandFailure
from moler.cmd.unix.useradd import Useradd


def test_useradd_returns_proper_command_string_user(buffer_connection):
    useradd_cmd = Useradd(connection=buffer_connection.moler_connection, user='xyz', options='-p 1234',
                          prompt=None, new_line_chars=None)
    assert "useradd -p 1234 xyz" == useradd_cmd.command_string


def test_useradd_returns_proper_command_string_defaults(buffer_connection):
    useradd_cmd = Useradd(connection=buffer_connection.moler_connection, defaults=True, options='-e 2018-08-01',
                          prompt=None, new_line_chars=None)
    assert "useradd -D -e 2018-08-01" == useradd_cmd.command_string


def test_useradd_raise_command_error(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_error()
    buffer_connection.remote_inject_response([command_output])
    useradd_cmd = Useradd(connection=buffer_connection.moler_connection,
                          defaults=True, options='-p', prompt=None, new_line_chars=None)
    assert "useradd -D -p" == useradd_cmd.command_string
    with pytest.raises(CommandFailure):
        useradd_cmd()


def test_useradd_raise_command_error_with_help(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_error_help()
    buffer_connection.remote_inject_response([command_output])
    useradd_cmd = Useradd(connection=buffer_connection.moler_connection,
                          user='xyz', options='-p', prompt=None, new_line_chars=None)
    assert "useradd -p xyz" == useradd_cmd.command_string
    with pytest.raises(CommandFailure):
        useradd_cmd()


@pytest.fixture
def command_output_and_expected_result_error():
    data = """xyz@debian:~$ useradd -D -p
useradd: option requires an argument -- 'p'
Usage: useradd [options] LOGIN
useradd -D
useradd -D [options]
xyz@debian:~$"""
    result = dict()
    return data, result


@pytest.fixture
def command_output_and_expected_result_error_help():
    data = """xyz@debian:~$ useradd -p xyz
Usage: useradd [options] LOGIN
useradd -D
useradd -D [options]
xyz@debian:~$"""
    result = dict()
    return data, result
