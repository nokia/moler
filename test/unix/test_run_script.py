# -*- coding: utf-8 -*-
"""
Which command test module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
from moler.exceptions import CommandFailure
from moler.cmd.unix.run_script import RunScript


def test_run_script_cmd_returns_proper_command_string(buffer_connection):
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh")
    assert "./myScript.sh" == cmd.command_string


def test_run_script_raise_exception(buffer_connection):
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh")
    with pytest.raises(CommandFailure):
        cmd()


def test_run_script_not_raise_exception(buffer_connection):
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh", error_regex=None)
    result = cmd()
    assert not result


@pytest.fixture
def command_output_and_expected_result():
    data = """ute@debdev:~$ ./myScript.sh
ERROR: wrong data
ute@debdev:~$"""
    result = dict()
    return data, result
