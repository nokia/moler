# -*- coding: utf-8 -*-
"""
Wget command test module.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


from moler.exceptions import CommandFailure
from moler.cmd.unix.wget import Wget
import pytest


def test_wget_returns_proper_command_string(buffer_connection):
    wget_cmd = Wget(connection=buffer_connection.moler_connection,
                    options='http://ftp.gnu.org/gnu/wget/wget-1.5.3.tar.gz')
    assert "wget http://ftp.gnu.org/gnu/wget/wget-1.5.3.tar.gz" == wget_cmd.command_string


def test_wget_raises_connection_failure(buffer_connection, command_output_and_expected_result_connection_failure):
    command_output, expected_result = command_output_and_expected_result_connection_failure
    buffer_connection.remote_inject_response([command_output])
    wget_cmd = Wget(connection=buffer_connection.moler_connection, options="https://moler.google.com")
    with pytest.raises(CommandFailure):
        wget_cmd()


@pytest.fixture
def command_output_and_expected_result_connection_failure():
    data = """moler@debian:~$ wget https://moler.google.com
--2018-09-14 12:25:22--  https://moler.google.com
Resolving moler.google.com (moler.google.com)... 172.217.21.110, 2a00:1460:4001:81d::300e
Connecting to moler.google.com (moler.google.com)|172.217.21.110|:443... failed: Connection timed out.
Connecting to moler.google.com (moler.google.com)|2a00:1460:4001:81d::300e|:443... failed: Network is unreachable.
moler@debian:~$"""
    result = dict()
    return data, result


def test_wget_raises_command_error(buffer_connection, command_output_and_expected_result_command_error):
    command_output, expected_result = command_output_and_expected_result_command_error
    buffer_connection.remote_inject_response([command_output])
    wget_cmd = Wget(connection=buffer_connection.moler_connection, options="-m", timeout=30)
    with pytest.raises(CommandFailure):
        wget_cmd()


@pytest.fixture
def command_output_and_expected_result_command_error():
    data = """moler@debian:~$ wget -m
wget: missing URL
Usage: wget [OPTION]... [URL]...
moler@debian:~$"""
    result = dict()
    return data, result
