# -*- coding: utf-8 -*-
"""
Testing of ln command.
"""
__author__ = 'Szymon Czaplak'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'szymon.czaplak@nokia.com'

import pytest
from moler.exceptions import CommandFailure


def test_journalctl_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.journalctl import Journalctl
    journalctl_cmd = Journalctl(connection=buffer_connection, options="--system")
    assert "journalctl --system" == journalctl_cmd.command_string


def test_calling_journalctl_raise_exception_command_failure(buffer_connection,
                                                            command_output_and_expected_result_no_permit):
        from moler.cmd.unix.journalctl import Journalctl
        command_output, expected_result = command_output_and_expected_result_no_permit
        buffer_connection.remote_inject_response([command_output])
        journalctl_cmd = Journalctl(connection=buffer_connection.moler_connection, options="--system")
        with pytest.raises(CommandFailure) as exception:
            journalctl_cmd()
        assert exception is not None

@pytest.fixture
def command_output_and_expected_result_no_permit():
    data = """
    user@server:~$ journalctl --system
    Hint: You are currently not seeing messages from other users and the system.
      Users in the 'systemd-journal' group can see all messages. Pass -q to
      turn off this notice.
    No journal files were opened due to insufficient permissions.
    user@server:~$"""
    result = {

    }
    return data, result
