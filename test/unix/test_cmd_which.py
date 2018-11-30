# -*- coding: utf-8 -*-
"""
Which command test module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'

import pytest
from moler.cmd.unix.which import Which
from moler.exceptions import CommandFailure


def test_which_returns_proper_command_string(buffer_connection):
    which_cmd = Which(connection=buffer_connection.moler_connection, names=["uname", "git", "firefox"])
    assert "which uname git firefox" == which_cmd.command_string


def test_which_returns_proper_command_string_show_all(buffer_connection):
    which_cmd = Which(connection=buffer_connection.moler_connection, show_all=True, names=["man"])
    assert "which -a man" == which_cmd.command_string


def test_which_raise_exception_empty_name(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    which_cmd = Which(connection=buffer_connection.moler_connection, names=["abc", ""])
    with pytest.raises(CommandFailure):
        which_cmd()


@pytest.fixture
def command_output_and_expected_result():
    data = """xyz@debian:~$ which abc
xyz@debian:~$"""
    result = dict()
    return data, result
