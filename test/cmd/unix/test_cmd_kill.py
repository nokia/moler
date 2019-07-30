# -*- coding: utf-8 -*-
"""
Testing of Kill command.
"""

__author__ = 'Yeshu Yang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yeshu.yang@nokia-sbell.com'

import pytest
from moler.exceptions import CommandFailure


def test_calling_kill_returns_result_no_permit(buffer_connection, command_output_and_expected_result_no_permit):
    from moler.cmd.unix.kill import Kill
    command_output, expected_result = command_output_and_expected_result_no_permit
    buffer_connection.remote_inject_response([command_output])
    kill_cmd = Kill(connection=buffer_connection.moler_connection, options="-9", pid="46911")
    with pytest.raises(CommandFailure):
        kill_cmd()


def test_kill_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.kill import Kill
    kill_cmd = Kill(buffer_connection, options="-9", pid="46911")
    assert "kill -9 46911" == kill_cmd.command_string

# --------------------------- resources


@pytest.fixture
def command_output_and_expected_result_no_permit():
    data = """
 host:~ # kill -9 46911
-bash: kill: (46911) - Operation not permitted
 host:~ # """

    result = {}
    return data, result
