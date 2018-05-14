# -*- coding: utf-8 -*-
"""
Testing of Killall command.
"""
__author__ = 'Yeshu Yang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yeshu.yang@nokia.com'

from moler.exceptions import CommandFailure
import pytest


def test_calling_killall_returns_result_no_permit(buffer_connection):
    from moler.cmd.unix.killall import Killall
    command_output, expected_result = command_output_and_expected_result_no_permit()
    buffer_connection.remote_inject_response([command_output])
    killall_cmd = Killall(connection=buffer_connection.moler_connection, name="iperf")
    try:
        killall_cmd()
    except CommandFailure as e:
        assert "Command failed 'killall iperf' with ERROR: Operation not permitted" == e.args[0]


def test_calling_df_returns_result_verbose(buffer_connection):
    from moler.cmd.unix.killall import Killall
    command_output, expected_result = command_output_and_expected_result_verbose()
    buffer_connection.remote_inject_response([command_output])
    killall_cmd = Killall(connection=buffer_connection.moler_connection, is_verbose="-v", name="iperf")
    result = killall_cmd()
    assert result == expected_result


def test_calling_df_returns_result_no_verbose(buffer_connection):
    from moler.cmd.unix.killall import Killall
    command_output, expected_result = command_output_and_expected_result_no_verbose()
    buffer_connection.remote_inject_response([command_output])
    killall_cmd = Killall(connection=buffer_connection.moler_connection, name="iperf")
    result = killall_cmd()
    assert result == expected_result


def test_calling_df_returns_result_no_process(buffer_connection):
    from moler.cmd.unix.killall import Killall
    command_output, expected_result = command_output_and_expected_result_no_process()
    buffer_connection.remote_inject_response([command_output])
    killall_cmd = Killall(connection=buffer_connection.moler_connection, name="tshark")
    result = killall_cmd()
    assert result == expected_result


def test_killall_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.killall import Killall
    killall_cmd = Killall(buffer_connection, name="iperf", is_verbose=None)
    assert "killall iperf" == killall_cmd.command_string

# --------------------------- resources


@pytest.fixture
def command_output_and_expected_result_no_permit():
    data = """
[emssim@Pclinux90: ~]$ killall iperf
iperf(14820): Operation not permitted
iperf(14823): Operation not permitted
iperf: no process killed
[emssim@Pclinux90: ~]$"""

    result = {}
    return data, result


@pytest.fixture
def command_output_and_expected_result_verbose():
    from moler.cmd.unix.killall import COMMAND_OUTPUT_verbose, COMMAND_RESULT_verbose
    data = COMMAND_OUTPUT_verbose
    result = COMMAND_RESULT_verbose
    return data, result


@pytest.fixture
def command_output_and_expected_result_no_verbose():
    from moler.cmd.unix.killall import COMMAND_OUTPUT_no_verbose, COMMAND_RESULT_no_verbose
    data = COMMAND_OUTPUT_no_verbose
    result = COMMAND_RESULT_no_verbose
    return data, result


@pytest.fixture
def command_output_and_expected_result_no_process():
    from moler.cmd.unix.killall import COMMAND_OUTPUT_no_process, COMMAND_RESULT_no_process
    data = COMMAND_OUTPUT_no_process
    result = COMMAND_RESULT_no_process
    return data, result
