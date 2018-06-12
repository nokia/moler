# -*- coding: utf-8 -*-
"""
Testing of ln command.
"""
__author__ = 'Haili Guo'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'haili.guo@nokia-sbell.com'

import pytest
from moler.exceptions import CommandFailure


def test_ln_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.ln import Ln
    ln_cmd = Ln(connection=buffer_connection.moler_connection, options="-s file1 file2")
    assert "ln -s file1 file2" == ln_cmd.command_string


def test_calling_ln_raise_exception_wrong_command_string(buffer_connection):
        from moler.cmd.unix.ln import Ln
        command_output, expected_result = command_output_and_expected_result_file_exist()
        buffer_connection.remote_inject_response([command_output])
        ln_cmd = Ln(connection=buffer_connection.moler_connection, options="-s file1 file2")
        with pytest.raises(CommandFailure, match=r'Command failed \'ln -s file1 file2\' with ERROR: '
                                                 r'ln: failed to create symbolic link, File exists'):
            ln_cmd()


@pytest.fixture
def command_output_and_expected_result_file_exist():
    data = """
    user@server:~> ln -s file1 file2
    ln: failed to create symbolic link, File exists
    user@server:~> """
    result = {

    }
    return data, result