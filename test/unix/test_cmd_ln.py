# -*- coding: utf-8 -*-
"""
Testing of ln command.
"""
__author__ = 'Haili Guo'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'haili.guo@nokia-sbell.com'

import pytest

def test_calling_ln_returns_result_parsed_from_command_output(buffer_connection):
    from moler.cmd.unix.ln import Ln
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    ln_cmd = Ln(connection=buffer_connection.moler_connection, options="-s file1 file2")
    result = ln_cmd()
    assert result == expected_result


@pytest.fixture
def command_output_and_expected_result():
    data = """
user@server:~> ln -s file1 file2
user@server:~>"""
    result = {
    }
    return data, result
