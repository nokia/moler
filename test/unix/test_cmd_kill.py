# -*- coding: utf-8 -*-
"""
Testing of Kill command.
"""

__author__ = 'Yeshu Yang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yeshu.yang@nokia-sbell.com'

import pytest
from moler.exceptions import CommandFailure


def test_calling_df_returns_result_no_process(buffer_connection):
    from moler.cmd.unix.kill import Kill
    command_output, expected_result = command_output_and_expected_result_no_process()
    buffer_connection.remote_inject_response([command_output])
    kill_cmd = Kill(connection=buffer_connection.moler_connection, options="-9", pid="973")
    result = kill_cmd()
    assert result == expected_result


def test_calling_kill_returns_result(buffer_connection):
    from moler.cmd.unix.kill import Kill
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    kill_cmd = Kill(connection=buffer_connection.moler_connection,pid="637")
    result = kill_cmd()
    assert result == expected_result


def test_calling_kill_returns_result_no_permit(buffer_connection):
    from moler.cmd.unix.kill import Kill
    command_output, expected_result = command_output_and_expected_result_no_permit()
    buffer_connection.remote_inject_response([command_output])
    kill_cmd = Kill(connection=buffer_connection.moler_connection, options="-9", pid="46911")
    try:
        kill_cmd()
    except CommandFailure as e:
        assert "Command failed 'kill -9 46911' with ERROR: Operation not permitted" == e.args[0]

# --------------------------- resources


@pytest.fixture
def command_output_and_expected_result_no_process():
    from moler.cmd.unix.kill import COMMAND_OUTPUT_no_process, COMMAND_RESULT_no_process
    data = COMMAND_OUTPUT_no_process
    result = COMMAND_RESULT_no_process
    return data, result


@pytest.fixture
def command_output_and_expected_result():
    from moler.cmd.unix.kill import COMMAND_OUTPUT, COMMAND_RESULT
    data = COMMAND_OUTPUT
    result = COMMAND_RESULT
    return data, result


@pytest.fixture
def command_output_and_expected_result_no_permit():
    data = """
 host:~ # kill -9 46911
-bash: kill: (46911) - Operation not permitted
 host:~ # """

    result = {}
    return data, result
