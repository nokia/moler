# -*- coding: utf-8 -*-
"""
ReadStatus command test module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
from moler.exceptions import CommandFailure
from moler.cmd.pdu_aten.pdu.read_status import ReadStatus


def test_read_status_command_string(buffer_connection):
    expected_command_string = "read status o01 format"
    cmd = ReadStatus(connection=buffer_connection.moler_connection, outlet="o01", output_format="format")
    assert cmd.command_string == expected_command_string


def test_read_status_failure(buffer_connection, command_output):
    buffer_connection.remote_inject_response([command_output])
    expected_command_string = "read status o01 wrong_format"
    cmd = ReadStatus(connection=buffer_connection.moler_connection, outlet="o01", output_format="wrong_format")
    assert cmd.command_string == expected_command_string
    with pytest.raises(CommandFailure):
        cmd()


@pytest.fixture
def command_output():
    data = """read status o01 wrong_format

Invalid command or exceed max command length

>"""
    return data
