# -*- coding: utf-8 -*-
"""
Testing of zip command.
"""
__author__ = 'Haili Guo'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'haili.guo@nokia-sbell.com'

import pytest

from moler.exceptions import CommandFailure


def test_zip_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.zip import Zip
    zip_cmd = Zip(buffer_connection, options="-r", zip_file="test.zip", file_name="test.txt")
    assert "zip -r test.zip test.txt" == zip_cmd.command_string


def test_calling_zip_raise_exception_wrong_command_string(buffer_connection, command_output_and_expected_result_file_not_exist):
    from moler.cmd.unix.zip import Zip
    command_output, expected_result = command_output_and_expected_result_file_not_exist
    buffer_connection.remote_inject_response([command_output])
    zip_cmd = Zip(connection=buffer_connection.moler_connection, options="", zip_file="test.zip", file_name="test.txt")
    with pytest.raises(CommandFailure, match=r"Command failed 'zip test.zip test.txt' with ERROR: "r'zip error: Nothing to do! \(test.zip\)'):
        zip_cmd()


def test_zip_raise_exception_wrong_command_string(buffer_connection):
    from moler.cmd.unix.zip import Zip
    with pytest.raises(TypeError, match=r'.*missing \d+ required positional argument.*|__init__\(\) takes at least \d+ arguments \(\d+ given\)'):
        Zip(buffer_connection, options="").command_string


def test_calling_zip_timeout(buffer_connection, command_output_and_expected_result_timeout):
    from moler.cmd.unix.zip import Zip
    command_output, expected_result = command_output_and_expected_result_timeout
    buffer_connection.remote_inject_response([command_output])
    zip_cmd = Zip(connection=buffer_connection.moler_connection, options="", zip_file="test.zip", file_name="test.txt")
    from moler.exceptions import CommandTimeout
    with pytest.raises(CommandTimeout) as exception:
        zip_cmd(timeout=0.5)
    assert exception is not None


@pytest.fixture
def command_output_and_expected_result_file_not_exist():
    data = """
    user@server:~> zip test.zip test.txt
    zip error: Nothing to do! (test.zip)
    user@server:~> """
    result = {

    }
    return data, result


@pytest.fixture
def command_output_and_expected_result_timeout():
    data = """
    user@server:~> zip test.zip test.txt
    """
    result={}
    return data, result
