# -*- coding: utf-8 -*-
"""
Userdel test module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import pytest

from moler.exceptions import CommandFailure
from moler.cmd.unix.userdel import Userdel


def test_userdel_returns_proper_command_string(buffer_connection):
    userdel_cmd = Userdel(connection=buffer_connection.moler_connection, user='xyz', prompt=None, new_line_chars=None)
    assert "userdel xyz" == userdel_cmd.command_string


def test_userdel_raises_command_error(buffer_connection):
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    userdel_cmd = Userdel(connection=buffer_connection.moler_connection, user='xyz', prompt=None, new_line_chars=None)
    with pytest.raises(CommandFailure):
        userdel_cmd()


@pytest.fixture
def command_output_and_expected_result():
    data = """xyz@debian:~$ userdel xyz
userdel: user bylica is currently used by process 788
xyz@debian:~$"""
    result = dict()
    return data, result

