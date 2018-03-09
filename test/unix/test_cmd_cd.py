# -*- coding: utf-8 -*-
"""
Testing of Yelnet command.
"""
__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'


def test_calling_uptime_returns_result_parsed_from_command_output(buffer_connection):
    from moler.cmd.unix.cd import Cd
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    cd_cmd = Cd(connection=buffer_connection.moler_connection)
    result = cd_cmd()
    assert result == expected_result


def command_output_and_expected_result():
    data = """
fzm-tdd-1:~ # cd /home/ute/
fzm-tdd-1:/home/ute #  
    """
    result = {
             }
    return data, result
