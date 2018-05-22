# -*- coding: utf-8 -*-
"""
Testing of Pkill command.
"""
__author__ = 'Yeshu Yang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yeshu.yang@nokia.com'

from moler.exceptions import CommandFailure
import pytest


def test_calling_pkill_returns_result_no_permit(buffer_connection):
    from moler.cmd.unix.pkill import Pkill
    command_output, expected_result = command_output_and_expected_result_no_permit()
    buffer_connection.remote_inject_response([command_output])
    pkill_cmd = Pkill(connection=buffer_connection.moler_connection, name="ping")
    with pytest.raises(CommandFailure, match=r'Command failed \'pkill ping\' with ERROR: Operation not permitted'):
        pkill_cmd()


def test_pkill_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.pkill import Pkill
    pkill_cmd = Pkill(buffer_connection, name="iperf")
    assert "pkill iperf" == pkill_cmd.command_string

# --------------------------- resources


@pytest.fixture
def command_output_and_expected_result_no_permit():
    data = """
ute@cp19-nj:~$ pkill ping
pkill: killing pid 64579 failed: Operation not permitted
pkill: killing pid 64727 failed: Operation not permitted
ute@cp19-nj:~$ """
    result = {}
    return data, result



