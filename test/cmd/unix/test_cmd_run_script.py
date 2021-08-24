# -*- coding: utf-8 -*-
"""
RunScript command test module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
from moler.exceptions import CommandFailure
from moler.cmd.unix.run_script import RunScript


def test_run_script_cmd_returns_proper_command_string(buffer_connection):
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh")
    assert "./myScript.sh" == cmd.command_string


def test_run_script_raise_exception(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh")
    with pytest.raises(CommandFailure):
        cmd()


def test_run_script_raise_exception_wrong_output(buffer_connection, command_output_lines):
    command_output, expected_result = command_output_lines
    buffer_connection.remote_inject_response([command_output])
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh",
                    success_regex="Line 3", error_regex=None)
    with pytest.raises(CommandFailure):
        cmd()


def test_run_script_proper_output(buffer_connection, command_output_lines):
    command_output, expected_result = command_output_lines
    buffer_connection.remote_inject_response([command_output])
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh",
                    success_regex=["Line 1", "Line 2"])
    result = cmd()
    assert result == expected_result


def test_run_script_not_raise_exception(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh", error_regex=None)
    result = cmd()
    assert not result


@pytest.fixture
def command_output_and_expected_result():
    data = """./myScript.sh
ERROR: wrong data
moler_bash#"""
    result = dict()
    return data, result


@pytest.fixture
def command_output_lines():
    data = """./myScript.sh
Line 1
Inter line
Line 2
moler_bash#"""
    result = dict()
    return data, result
