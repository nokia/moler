# -*- coding: utf-8 -*-
"""
Testing of cd command.
"""
__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'


def test_calling_uptime_returns_result_parsed_from_command_output(buffer_connection):
    from moler.cmd.unix.cd import Cd
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    cd_cmd = Cd(connection=buffer_connection.moler_connection, path="/home/user/")
    result = cd_cmd()
    assert result == expected_result


def test_cd_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.cd import Cd
    cd_cmd = Cd(connection=buffer_connection.moler_connection, path="/home/user/")
    assert "cd /home/user/" == cd_cmd.command_string


def command_output_and_expected_result():
    data = """
host:~ # cd /home/user/
host:/home/user #  
    """
    result = {
    }
    return data, result
