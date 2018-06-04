# -*- coding: utf-8 -*-
"""
Testing of mkdir command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

from moler.cmd.unix.mkdir import Mkdir


def test_calling_mkdir_returns_result_parsed_from_command_output(buffer_connection):
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])

    mkdir_cmd = Mkdir(connection=buffer_connection.moler_connection, path="/home/ute/test")
    result = mkdir_cmd()
    assert result == expected_result


def test_mkdir_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.mkdir import Mkdir
    mkdir_cmd = Mkdir(connection=buffer_connection.moler_connection, path="/home/user/")
    assert "mkdir /home/user/" == mkdir_cmd.command_string


def command_output_and_expected_result():
    data = """
user@server:~> mkdir /home/ute/test
user@server:~>"""

    result = {
    }
    return data, result
