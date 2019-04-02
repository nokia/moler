# -*- coding: utf-8 -*-
"""
Testing of mv command.
"""
import pytest

__author__ = 'Maciej Malczyk, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'maciej.malczyk@nokia.com, marcin.usielski@nokia.com'


@pytest.mark.parametrize("source,destination,error", [
    ("1.txt", "1.txt", "mv: '1.txt' and '1.txt' are the same file"),
    ("/home/ute/1.txt", "/opt/", "mv: cannot create regular file '/opt/1.txt': Permission denied"),
    ("/opt/lua", "/opt/old_lua", "mv: cannot move '/opt/lua' to '/opt/old_lua': Permission denied"),
    ("/opt/btslog/assistant", "/home/ute/", "mv: cannot remove '/opt/btslog/assistant': Permission denied"),
    ("/opt/some_dir", "/home/ute/", "mv: cannot stat '/opt/some_dir': No such file or directory"),
])
def test_calling_mv_raises_exception_command_failure(source, destination, error, buffer_connection, command_output_and_expected_result):
    from moler.cmd.unix.mv import Mv
    from moler.exceptions import CommandFailure
    output_data, result = command_output_and_expected_result(source, destination, error)
    buffer_connection.remote_inject_response([output_data])
    mv_cmd = Mv(connection=buffer_connection.moler_connection, src=source, dst=destination)
    with pytest.raises(CommandFailure):
        result = mv_cmd()
        assert result == result


def test_mv_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.mv import Mv
    mv_cmd = Mv(connection=buffer_connection.moler_connection, src='/home/ute/robotlte', dst='/home/ute/trunk')
    assert "mv /home/ute/robotlte /home/ute/trunk" == mv_cmd.command_string


@pytest.fixture
def command_output_and_expected_result():
    def output_data(src, dst, err):
        data = """
        ute@debdev:~$ mv {} {}
        {}
        ute@debdev:~$ """
        result = {}
        return data.format(src, dst, err), result

    return output_data
