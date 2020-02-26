# -*- coding: utf-8 -*-
"""
Testing of uptime command.
"""
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
from moler.exceptions import CommandFailure
from moler.exceptions import CommandTimeout


def test_calling_uptime_returns_result_parsed_from_command_output(buffer_connection,
                                                                  command_output_and_expected_result):
    from moler.cmd.unix.uptime import Uptime
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    uptime_cmd = Uptime(connection=buffer_connection.moler_connection)
    result = uptime_cmd()
    assert result == expected_result


def test_calling_uptime_fails_unsupported_format(buffer_connection, command_unsupported_output):
    from moler.cmd.unix.uptime import Uptime
    command_output = command_unsupported_output
    buffer_connection.remote_inject_response([command_output])
    uptime_cmd = Uptime(connection=buffer_connection.moler_connection)
    with pytest.raises(CommandFailure):
        uptime_cmd()


def test_calling_uptime_timeout(buffer_connection):
    from moler.cmd.unix.uptime import Uptime
    uptime_cmd = Uptime(connection=buffer_connection.moler_connection)
    uptime_cmd.terminating_timeout = 0.2
    uptime_cmd.timeout = 0.2
    with pytest.raises(CommandTimeout):
        uptime_cmd()

def test_uptime_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.uptime import Uptime
    uptime_cmd = Uptime(buffer_connection.moler_connection)
    assert "uptime" == uptime_cmd.command_string


def test_uptime_sends_with_enter(buffer_connection):
    from moler.cmd.unix.uptime import Uptime
    uptime_cmd = Uptime(buffer_connection.moler_connection)
    uptime_cmd.send_command()


def test_uptime_sends_without_enter(buffer_connection):
    from moler.cmd.unix.uptime import Uptime
    uptime_cmd = Uptime(buffer_connection.moler_connection)
    uptime_cmd.newline_after_command_string = False
    uptime_cmd.send_command()


@pytest.fixture
def command_output_and_expected_result():
    data = """
host:~ # uptime
 10:38am  up 3 days  2:14,  29 users,  load average: 0.09, 0.10, 0.07
host:~ #"""

    result = {
        "UPTIME": '3 days  2:14',
        "UPTIME_SECONDS": 267240,
        "USERS": 29,
    }
    return data, result


@pytest.fixture
def command_unsupported_output():
    data = """
host:~ # uptime
 10:38am  up UNSUPPORTED FORMAT,  29 users,  load average: 0.09, 0.10, 0.07
host:~ #"""

    return data
