# -*- coding: utf-8 -*-
"""
Testing of ln command.
"""
__author__ = 'Haili Guo'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'haili.guo@nokia-sbell.com'

import pytest
from moler.exceptions import CommandFailure


def test_journalctl_returns_proper_command_string():
    from moler.cmd.unix.journalctl import Journalctl
    journalctl_cmd = Journalctl(options="--system")
    assert "journalctl --system" == journalctl_cmd.command_string


def test_calling_ln_raise_exception_command_failure(buffer_connection, command_output_and_expected_result_file_exist):
        from moler.cmd.unix.journalctl import Journalctl
        command_output, expected_result = command_output_and_expected_result_file_exist
        buffer_connection.remote_inject_response([command_output])
        ln_cmd = Journalctl(options="-s file1 file2")
        with pytest.raises(CommandFailure):
            ln_cmd()


@pytest.fixture
def command_output_and_expected_result_file_exist():
    data = """
    ute@sc5g-gnb-026:~$ journalctl --system
    Hint: You are currently not seeing messages from other users and the system.
      Users in the 'systemd-journal' group can see all messages. Pass -q to
      turn off this notice.
    No journal files were opened due to insufficient permissions.
    """
    result = {

    }
    return data, result
