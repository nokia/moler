# -*- coding: utf-8 -*-
"""
Testing of mv command.
"""
import pytest

__author__ = 'Maciej Malczyk'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'maciej.malczyk@nokia.com'

DATA = """
ute@debdev:~$ mv {} {}
ute@debdev:~$ {}
    """
RESULT = {}


def test_calling_mv_returns_result_parsed_from_command_output(buffer_connection):
    from moler.cmd.unix.mv import Mv
    buffer_connection.remote_inject_response([DATA.format('test', 'moved_test', '')])
    mv_cmd = Mv(connection=buffer_connection.moler_connection, src='test', dst='moved_test')
    result = mv_cmd()
    assert result == RESULT


@pytest.mark.parametrize("source,destination,error", [
    ("1.txt", "1.txt", "mv: '1.txt' and '1.txt' are the same file"),
    ("/home/ute/1.txt", "/opt/", "mv: cannot create regular file '/opt/1.txt': Permission denied"),
    ("/opt/lua", "/opt/old_lua", "mv: cannot move '/opt/lua' to '/opt/old_lua': Permission denied"),
    ("/opt/btslog/assistant", "/home/ute/", "mv: cannot remove '/opt/btslog/assistant': Permission denied"),
    ("/opt/some_dir", "/home/ute/", "mv: cannot stat '/opt/some_dir': No such file or directory"),
])
def test_calling_mv_raises_exception_command_failure(source, destination, error, buffer_connection):
    from moler.cmd.unix.mv import Mv
    from moler.exceptions import CommandFailure
    buffer_connection.remote_inject_response([DATA.format(source, destination, error)])
    mv_cmd = Mv(connection=buffer_connection.moler_connection, src=source, dst=destination)
    with pytest.raises(CommandFailure):
        result = mv_cmd()
        assert result == RESULT


def test_cd_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.mv import Mv
    mv_cmd = Mv(connection=buffer_connection.moler_connection, src='/home/ute/robotlte', dst='/home/ute/trunk')
    assert "mv /home/ute/robotlte /home/ute/trunk" == mv_cmd.command_string
