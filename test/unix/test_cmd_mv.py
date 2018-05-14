# -*- coding: utf-8 -*-
"""
Testing of mv command.
"""
__author__ = 'Maciej Malczyk'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'maciej.malczyk@nokia.com'


def test_calling_mv_returns_result_parsed_from_command_output(buffer_connection):
    from moler.cmd.unix.mv import Mv
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    mv_cmd = Mv(connection=buffer_connection.moler_connection, src='test', dst='moved_test')
    result = mv_cmd()
    assert result == expected_result


def test_cd_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.mv import Mv
    mv_cmd = Mv(connection=buffer_connection.moler_connection, src='/home/ute/robotlte', dst='/home/ute/trunk')
    assert "mv /home/ute/robotlte /home/ute/trunk" == mv_cmd.command_string


def command_output_and_expected_result():
    data = """
ute@debdev:~$ mv test moved_test
ute@debdev:~$
    """
    result = {
    }
    return data, result
