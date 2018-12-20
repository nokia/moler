# -*- coding: utf-8 -*-
"""
Testing of uptime command.
"""
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
import time
from moler.event_awaiter import EventAwaiter


def test_two_commands_uptime_whoami(buffer_connection, command_output_and_expected_result_uptime_whoami):
    from moler.cmd.unix.uptime import Uptime
    from moler.cmd.unix.whoami import Whoami
    command_output, expected_result = command_output_and_expected_result_uptime_whoami
    uptime_cmd = Uptime(connection=buffer_connection.moler_connection)
    whoami_cmd = Whoami(connection=buffer_connection.moler_connection)
    uptime_cmd.start(timeout=2)
    whoami_cmd.start(timeout=2)
    buffer_connection.moler_connection.data_received(command_output[0].encode("utf-8"))
    time.sleep(0.2)
    buffer_connection.moler_connection.data_received(command_output[1].encode("utf-8"))
    assert EventAwaiter.wait_for_all(timeout=2, events=[uptime_cmd, whoami_cmd]) is True
    ret_uptime = uptime_cmd.result()
    ret_whoami = whoami_cmd.result()
    assert ret_uptime == expected_result[0]
    assert ret_whoami == expected_result[1]


def test_two_commands_uptime(buffer_connection, command_output_and_expected_result_uptime):
    from moler.cmd.unix.uptime import Uptime
    command_output, expected_result = command_output_and_expected_result_uptime
    uptime1_cmd = Uptime(connection=buffer_connection.moler_connection, prompt="host:.*#")
    uptime2_cmd = Uptime(connection=buffer_connection.moler_connection, prompt="host:.*#")
    uptime1_cmd.start(timeout=2)
    uptime2_cmd.start(timeout=2)
    buffer_connection.moler_connection.data_received(command_output[0].encode("utf-8"))
    time.sleep(0.2)
    buffer_connection.moler_connection.data_received(command_output[1].encode("utf-8"))
    assert EventAwaiter.wait_for_all(timeout=2, events=(uptime1_cmd, uptime2_cmd)) is True
    uptime1_ret = uptime1_cmd.result()
    uptime2_ret = uptime2_cmd.result()
    assert uptime1_ret == expected_result[0]
    assert uptime2_ret == expected_result[1]


@pytest.fixture
def command_output_and_expected_result_uptime_whoami():
    data = ("""uptime
 10:38am  up 3 days  2:14,  29 users,  load average: 0.09, 0.10, 0.07
host:~ # """,
            """whoami
user
host:~ # """)

    result = (
        {
            "UPTIME": '3 days  2:14',
            "UPTIME_SECONDS": 8040,
            "USERS": 29,
        },
        {
            "USER": "user"
        }
    )
    return data, result


@pytest.fixture
def command_output_and_expected_result_uptime():
    data = (
"""host:~ # uptime
 10:38am  up 3 days  2:14,  29 users,  load average: 0.09, 0.10, 0.07
host:~ # """,
"""uptime
10:38am  up 3 days  2:15,  8 users,  load average: 0.09, 0.10, 0.07
host:~ # """)

    result = (
        {
            "UPTIME": '3 days  2:14',
            "UPTIME_SECONDS": 8040,
            "USERS": 29,
        },
        {
            "UPTIME": '3 days  2:15',
            "UPTIME_SECONDS": 8100,
            "USERS": 8,
        }
    )
    return data, result
