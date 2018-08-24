# -*- coding: utf-8 -*-
"""
Testing of chmod command.
"""
import pytest

__author__ = 'Yuping Sang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yuping.sang@nokia.com'


@pytest.mark.parametrize("permission, filename, error", [

    ("777", "/home/ute/test.txt", "chmod: changing permissions of test.txt: operation not permitted"),
    ("777", "/root/test1.txt", "chmod: cannot access /root/test1.txt:  No such file or director'"),
    ("777", "/root/test.txt", "chmod: WARNING: can't change"),
])
def test_calling_chmod_raises_exception_command_failure(permission, filename, error, buffer_connection, command_output_and_expected_result):
    from moler.cmd.unix.chmod import Chmod
    from moler.exceptions import CommandFailure
    output_data, result = command_output_and_expected_result(permission, filename, error)
    buffer_connection.remote_inject_response([output_data])
    chmod_cmd = Chmod(connection=buffer_connection.moler_connection, permission=permission, filename=filename)
    with pytest.raises(CommandFailure):
        result = chmod_cmd()
        assert result == result


def test_chmod_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.chmod import Chmod
    mv_cmd = Chmod(connection=buffer_connection.moler_connection, permission='777', filename='/home/ute/test.txt')
    assert "chmod 777 /home/ute/test.txt" == mv_cmd.command_string


@pytest.fixture
def command_output_and_expected_result():
    def output_data(permission, filename, error):
        data = """
        ute@debdev:~$ chmod {} {}
        ute@debdev:~$ {}
            """
        result = {}
        return data.format(permission, filename, error), result

    return output_data
