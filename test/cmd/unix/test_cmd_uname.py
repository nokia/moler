# -*- coding: utf-8 -*-
"""
Testing of uname command.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


from moler.exceptions import CommandFailure
from moler.cmd.unix.uname import Uname
import pytest


def test_uname_returns_proper_command_string(buffer_connection):
    uname_cmd = Uname(connection=buffer_connection.moler_connection, options="-a")
    assert "uname -a" == uname_cmd.command_string


def test_uname_raise_exception_wrong_option(buffer_connection, command_output_and_expected_result_option):
    command_output, expected_result = command_output_and_expected_result_option
    buffer_connection.remote_inject_response([command_output])
    uname_cmd = Uname(connection=buffer_connection.moler_connection, options="-pk")
    with pytest.raises(CommandFailure):
        uname_cmd()


def test_uname_raise_exception_wrong_command(buffer_connection, command_output_and_expected_result_command):
    command_output, expected_result = command_output_and_expected_result_command
    buffer_connection.remote_inject_response([command_output])
    uname_cmd = Uname(connection=buffer_connection.moler_connection, options="gh")
    with pytest.raises(CommandFailure):
        uname_cmd()


@pytest.fixture
def command_output_and_expected_result_option():
    data = """xyz@debian:~/Moler/$ uname -pk
uname: invalid option -- 'k'
Try 'uname --help' for more information.
xyz@debian:~/Moler/$"""
    result = dict()
    return data, result


@pytest.fixture
def command_output_and_expected_result_command():
    data = """xyz@debian:~/Moler/$ uname gh
uname: extra operand 'gh'
Try 'uname --help' for more information.
xyz@debian:~/Moler/$"""
    result = dict()
    return data, result
