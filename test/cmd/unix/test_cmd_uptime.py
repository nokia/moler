# -*- coding: utf-8 -*-
"""
Testing of uptime command.
"""
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
import time
from moler.exceptions import CommandFailure
from moler.exceptions import CommandTimeout
from moler.cmd.unix.uptime import Uptime


def test_calling_uptime_returns_result_parsed_from_command_output(buffer_connection,
                                                                  command_output_and_expected_result):
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


def test_calling_uptime_timeout_with_long_timeout(buffer_connection):
    uptime_cmd = Uptime(connection=buffer_connection.moler_connection)
    long_timeout = 300
    uptime_cmd.terminating_timeout = 0.2
    uptime_cmd.start(timeout=long_timeout)
    uptime_cmd.timeout = long_timeout
    start_time = time.time()
    with pytest.raises(CommandTimeout):
        uptime_cmd.await_done(timeout=1)
    end_time = time.time()
    duration = end_time - start_time
    assert duration < long_timeout/10


def test_calling_uptime_timeout_with_short_timeout(buffer_connection):
    uptime_cmd = Uptime(connection=buffer_connection.moler_connection)
    short_timeout = 7
    uptime_cmd.terminating_timeout = 0.2
    uptime_cmd.start(timeout=short_timeout)
    start_time = time.time()
    with pytest.raises(CommandTimeout):
        uptime_cmd.await_done()
    end_time = time.time()
    duration = end_time - start_time
    assert duration < short_timeout + 1
    assert duration >= short_timeout


def test_calling_uptime_timeout(buffer_connection):
    uptime_cmd = Uptime(connection=buffer_connection.moler_connection)
    uptime_cmd.terminating_timeout = 0.2
    uptime_cmd.timeout = 0.2
    with pytest.raises(CommandTimeout):
        uptime_cmd()


def test_uptime_returns_proper_command_string(buffer_connection):
    uptime_cmd = Uptime(buffer_connection.moler_connection)
    assert "uptime" == uptime_cmd.command_string


def test_uptime_sends_with_enter(buffer_connection):
    uptime_cmd = Uptime(buffer_connection.moler_connection)
    uptime_cmd.send_command()


def test_uptime_sends_without_enter(buffer_connection):
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
