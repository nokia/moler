# -*- coding: utf-8 -*-
"""
Touch command test module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
from moler.cmd.unix.touch import Touch
from moler.exceptions import CommandFailure


def test_touch_cannot_create(buffer_connection):
    touch_cmd = Touch(connection=buffer_connection.moler_connection, path="file.asc")
    assert "touch file.asc" == touch_cmd.command_string
    command_output = "touch file.asc\ntouch: cannot touch 'file.asc': Permission denied\nmoler_bash#"
    buffer_connection.remote_inject_response([command_output])
    with pytest.raises(CommandFailure):
        touch_cmd()


def test_touch_read_only(buffer_connection):
    touch_cmd = Touch(connection=buffer_connection.moler_connection, path="file.asc")
    assert "touch file.asc" == touch_cmd.command_string
    command_output = "touch file.asc\ntouch: cannot touch 'file.asc': Read-only file system\nmoler_bash#"
    buffer_connection.remote_inject_response([command_output])
    with pytest.raises(CommandFailure):
        touch_cmd()


def test_touch_read_only_remove(buffer_connection):
    touch_cmd = Touch(connection=buffer_connection.moler_connection, path="file.asc")
    touch_cmd.re_fail = None
    touch_cmd.add_failure_indication("Read-only file system")
    assert "touch file.asc" == touch_cmd.command_string
    command_output = "touch file.asc\ntouch: cannot touch 'file.asc': Read-only file system\nmoler_bash#"
    buffer_connection.remote_inject_response([command_output])
    with pytest.raises(CommandFailure):
        touch_cmd()
