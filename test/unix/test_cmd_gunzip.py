# -*- coding: utf-8 -*-
"""
Gunzip command test module.
"""

__author__ = 'Adrianna Pienkowska, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com, marcin.usielski@nokia.com'

import pytest
import time
from moler.cmd.unix.gunzip import Gunzip
from moler.exceptions import CommandFailure, WrongUsage


def test_gunzip_returns_proper_command_string(buffer_connection):
     gunzip_cmd = Gunzip(buffer_connection, archive_name=["old.gz"])
     assert "gunzip old.gz" == gunzip_cmd.command_string


def test_gunzip_raise_error_on_wrong_option(buffer_connection, command_output_and_expected_result_on_wrong_option):
    gunzip_cmd = Gunzip(connection=buffer_connection.moler_connection, archive_name=["old.gz"], options='-b')
    command_output, expected_result = command_output_and_expected_result_on_wrong_option
    buffer_connection.remote_inject_response([command_output])
    assert 'gunzip -b old.gz' == gunzip_cmd.command_string
    with pytest.raises(CommandFailure):
        gunzip_cmd()


def test_gunzip_raise_error_on_no_such_file(buffer_connection, command_output_and_expected_result_on_no_such_file):
    gunzip_cmd = Gunzip(connection=buffer_connection.moler_connection, archive_name=["new5.gz"])
    command_output, expected_result = command_output_and_expected_result_on_no_such_file
    buffer_connection.remote_inject_response([command_output])
    assert 'gunzip new5.gz' == gunzip_cmd.command_string
    with pytest.raises(CommandFailure):
        gunzip_cmd()


def test_gunzip_raise_error_on_cannot_overwrite(buffer_connection, command_output_and_expected_result_on_cannot_overwrite):
    gunzip_cmd = Gunzip(connection=buffer_connection.moler_connection, archive_name=["new5.gz"])
    command_output, expected_result = command_output_and_expected_result_on_cannot_overwrite
    buffer_connection.remote_inject_response([command_output])
    assert 'gunzip new5.gz' == gunzip_cmd.command_string
    with pytest.raises(CommandFailure):
        gunzip_cmd()


def test_gunzip_raise_error_on_cannot_overwrite_multiple_files(
        buffer_connection, command_output_and_expected_result_on_cannot_overwrite_multiple_files):
    gunzip_cmd = Gunzip(connection=buffer_connection.moler_connection, archive_name=["new5.gz", "new.gz"])
    assert 'gunzip new5.gz new.gz' == gunzip_cmd.command_string
    gunzip_cmd.start()
    time.sleep(0.1)
    command_output, expected_result = command_output_and_expected_result_on_cannot_overwrite_multiple_files
    for output in command_output:
        buffer_connection.moler_connection.data_received(output.encode("utf-8"))
    with pytest.raises(WrongUsage):
        gunzip_cmd()


def test_gunzip_raise_error_on_can_multiple_files(
        buffer_connection, command_output_and_expected_result_on_overwrite_multiple_files):
    gunzip_cmd = Gunzip(connection=buffer_connection.moler_connection,
                        archive_name=["new5.gz", "new.gz"], overwrite=True)
    assert 'gunzip new5.gz new.gz' == gunzip_cmd.command_string
    gunzip_cmd.start()
    time.sleep(0.1)
    command_output, expected_result = command_output_and_expected_result_on_overwrite_multiple_files
    for output in command_output:
        buffer_connection.moler_connection.data_received(output.encode("utf-8"))
    assert gunzip_cmd.done() is True


@pytest.fixture
def command_output_and_expected_result_on_wrong_option():
    output = """xyz@debian:~/Dokumenty/sed$ gunzip -b old.gz
gzip: -b operand is not an integer
Try `gzip --help' for more information.
xyz@debian:~/Dokumenty/sed$ """
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_on_no_such_file():
    output = """xyz@debian:~/Dokumenty/sed$ gunzip new5.gz
gzip: new5.gz: No such file or directory
xyz@debian:~/Dokumenty/sed$ """
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_on_cannot_overwrite():
    output = """xyz@debian:~/Dokumenty/sed$ gunzip new5.gz
gzip: new5 already exists; do you wish to overwrite (y or n)? xyz@debian:~/Dokumenty/sed$"""
    result = dict()
    return output, result

@pytest.fixture
def command_output_and_expected_result_on_cannot_overwrite_multiple_files():
    output = """xyz@debian:~/Dokumenty/sed$ gunzip new5.gz new.gz
gzip: new5 already exists; do you wish to overwrite (y or n)?"""
    output2 = """
gzip: new already exists; do you wish to overwrite (y or n)? xyz@debian:~/Dokumenty/sed$"""
    result = dict()
    return [output, output2], result


@pytest.fixture
def command_output_and_expected_result_on_overwrite_multiple_files():
    output = """xyz@debian:~/Dokumenty/sed$ gunzip new5.gz new.gz
gzip: new5 already exists; do you wish to overwrite (y or n)?"""
    output2 = """
gzip: new already exists; do you wish to overwrite (y or n)? xyz@debian:~/Dokumenty/sed$"""
    result = dict()
    return [output, output2], result
