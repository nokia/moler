# -*- coding: utf-8 -*-
"""
Testing of chown command.
"""
import pytest

__author__ = 'Yuping Sang, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'yuping.sang@nokia-sbell.com, marcin.usielski@nokia.com'


@pytest.mark.parametrize("param, filename, error", [

    (" ", "/rom/swconfig.txt", "chown: missing operand after ute,Try 'chown--help for more information"),
    ("ute", " ", "chown: missing operand after ute,Try 'chown--help for more information"),
    ("ute", "/root/test.txt", "chown: cannot access test.txt: No such file or director"),
    ("ute", "/root/test.txt", "chown: changing ownership of test.txt: Operation not Permitted")
])
def test_calling_chmod_raises_exception_command_failure(param, filename, error, buffer_connection,
                                                        command_output_and_expected_result):
    from moler.cmd.unix.chown import Chown
    from moler.exceptions import CommandFailure
    output_data, result = command_output_and_expected_result(param, filename, error)
    buffer_connection.remote_inject_response([output_data])
    chown_cmd = Chown(connection=buffer_connection.moler_connection, param=param, filename=filename)
    with pytest.raises(CommandFailure):
        result = chown_cmd()
        assert result == result


def test_chown_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.chown import Chown
    mv_cmd = Chown(connection=buffer_connection.moler_connection, param='ute', filename='/rom/swconfig.txt')
    assert "chown ute /rom/swconfig.txt" == mv_cmd.command_string


@pytest.fixture
def command_output_and_expected_result():
    def output_data(param, filename, error):
        data = """
        ute@debdev:~$ chown {} {}
        {}
        ute@debdev:~$"""
        result = {}
        return data.format(param, filename, error), result

    return output_data
