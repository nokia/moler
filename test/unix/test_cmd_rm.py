# -*- coding: utf-8 -*-
"""
Rm command module.
"""

__author__ = 'Bartosz Odziomek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'bartosz.odziomek@nokia.com'


def test_calling_rm_returns_result_parsed_from_command_output(buffer_connection):
    from moler.cmd.unix.rm import Rm
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    cd_cmd = Rm(connection=buffer_connection.moler_connection, file="test.txt", options="-R")
    result = cd_cmd()
    assert result == expected_result


def test_rm_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.rm import Rm
    rm_cmd = Rm(connection=buffer_connection.moler_connection, file="test.txt")
    assert "rm test.txt" == rm_cmd.command_string


def command_output_and_expected_result():
    data = """
user@server:~> rm -R test.txt
user@server:~> 
    """
    result = {
    }
    return data, result
