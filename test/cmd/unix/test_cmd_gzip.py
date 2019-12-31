# -*- coding: utf-8 -*-
"""
Gzip command test module.
"""

__author__ = 'Dawid Gwizdz'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'dawid.gwizdz@nokia.com'

import pytest
from moler.cmd.unix.gzip import Gzip
from moler.exceptions import CommandFailure


def test_gzip_returns_proper_command_string(buffer_connection):
    gzip_cmd = Gzip(buffer_connection, file_name="afile", options="-v", compressed_file_name="compressed_file.gz")
    assert "gzip -v afile -c > compressed_file.gz" == gzip_cmd.command_string


def test_gzip_raise_error_on_wrong_option(buffer_connection, command_output_on_wrong_option):
    gzip_cmd = Gzip(connection=buffer_connection.moler_connection, file_name="afile", options='--wrong_option')
    command_output = command_output_on_wrong_option
    buffer_connection.remote_inject_response([command_output])
    assert "gzip --wrong_option afile"
    with pytest.raises(CommandFailure):
        gzip_cmd()


def test_gzip_raise_error_on_no_such_file(buffer_connection, command_output_on_no_such_file):
    gzip_cmd = Gzip(connection=buffer_connection.moler_connection, file_name="file_which_no_exists")
    command_output = command_output_on_no_such_file
    buffer_connection.remote_inject_response([command_output])
    assert "gzip file_which_no_exists" == gzip_cmd.command_string
    with pytest.raises(CommandFailure):
        gzip_cmd()


def test_gzip_raise_error_on_cannot_overwrite(buffer_connection, command_output_on_cannot_overwrite):
    gzip_cmd = Gzip(connection=buffer_connection.moler_connection, file_name="afile")
    command_output = command_output_on_cannot_overwrite
    buffer_connection.remote_inject_response([command_output])
    assert 'gzip afile' == gzip_cmd.command_string
    with pytest.raises(CommandFailure):
        gzip_cmd()


@pytest.fixture
def command_output_on_wrong_option():
    output = """xyz@debian:~$ gzip --wrong_option afile
gzip: unrecognized option '--wrong_option'
Try `gzip --help' for more information.
xyz@debian:~$"""
    return output


@pytest.fixture
def command_output_on_no_such_file():
    output = """xyz@debian:~$ gzip file_which_no_exists
gzip: file_which_no_exists: No such file or directory
xyz@debian:~$"""
    return output


@pytest.fixture
def command_output_on_cannot_overwrite():
    output = """xyz@debian:~$ gzip afile
gzip: afile.gz already exists; do you wish to overwrite (y or n)? n
    not overwritten
xyz@debian:~$"""
    return output
