# -*- coding: utf-8 -*-
"""
Testing of uptime command.
"""
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest


def test_calling_uptime_returns_result_parsed_from_command_output(buffer_connection,
                                                                  command_output_and_expected_result):
    from moler.cmd.unix.uptime import Uptime
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    uptime_cmd = Uptime(connection=buffer_connection.moler_connection)
    result = uptime_cmd()
    assert result == expected_result


def test_uptime_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.uptime import Uptime
    uptime_cmd = Uptime(buffer_connection)
    assert "uptime" == uptime_cmd.command_string


@pytest.fixture
def command_output_and_expected_result():
    data = """
host:~ # uptime
 10:38am  up 3 days  2:14,  29 users,  load average: 0.09, 0.10, 0.07
host:~ #"""

    result = {
        "UPTIME": '3 days  2:14',
        "UPTIME_SECONDS": 8040,
        "USERS": 29,
    }
    return data, result
