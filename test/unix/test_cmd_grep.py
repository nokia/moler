# -*- coding: utf-8 -*-
"""
Testing of grep command.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
_email_ = 'julia.patacz@nokia.com'

import pytest

from moler.cmd.unix.grep import Grep


def test_calling_grep_returns_result_parsed_from_command_output_with_path_and_lines_number_and_bytes(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_with_path_and_lines_number_and_bytes()
    buffer_connection.remote_inject_response([command_output])
    grep_cmd = Grep(connection=buffer_connection.moler_connection, options='-bnH PREROUTING /etc/iptables/rules.v4')
    result = grep_cmd()
    assert expected_result == result


def test_calling_grep_returns_result_parsed_from_command_output_with_path_and_lines_number(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_with_path_and_lines_number()
    buffer_connection.remote_inject_response([command_output])
    grep_cmd = Grep(connection=buffer_connection.moler_connection, options='-nH PREROUTING /etc/iptables/rules.v4')
    result = grep_cmd()
    assert expected_result == result


def test_calling_grep_returns_result_parsed_from_command_output_with_path(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_with_path()
    buffer_connection.remote_inject_response([command_output])
    grep_cmd = Grep(connection=buffer_connection.moler_connection, options='-H PREROUTING /etc/iptables/rules.v4')
    result = grep_cmd()
    assert expected_result == result


def test_calling_grep_returns_result_parsed_from_command_output_with_lines_number_and_bytes(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_with_lines_number_and_bytes()
    buffer_connection.remote_inject_response([command_output])
    grep_cmd = Grep(connection=buffer_connection.moler_connection, options='-bn PREROUTING /etc/iptables/rules.v4')
    result = grep_cmd()
    assert expected_result == result


def test_calling_grep_returns_result_parsed_from_command_output_with_lines_number(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_with_lines_number()
    buffer_connection.remote_inject_response([command_output])
    grep_cmd = Grep(connection=buffer_connection.moler_connection, options='-n PREROUTING /etc/iptables/rules.v4')
    result = grep_cmd()
    assert expected_result == result


def test_calling_grep_returns_result_parsed_from_command_output(buffer_connection):
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    grep_cmd = Grep(connection=buffer_connection.moler_connection, options='Mode debconf.conf')
    result = grep_cmd()
    assert expected_result == result


def test_grep_returns_proper_command_string(buffer_connection):
    grep_cmd = Grep(buffer_connection, options="Mode debconf.conf")
    assert "grep Mode debconf.conf" == grep_cmd.command_string


@pytest.fixture
def command_output_and_expected_result_with_path_and_lines_number_and_bytes():
    from moler.cmd.unix.grep import COMMAND_OUTPUT_with_file_path_and_lines_number_and_bytes, \
        COMMAND_RESULT_with_file_path_and_lines_number_and_bytes
    data = COMMAND_OUTPUT_with_file_path_and_lines_number_and_bytes
    result = COMMAND_RESULT_with_file_path_and_lines_number_and_bytes
    return data, result


@pytest.fixture
def command_output_and_expected_result_with_path_and_lines_number():
    from moler.cmd.unix.grep import COMMAND_OUTPUT_with_file_path_and_lines_number_or_bytes, \
        COMMAND_RESULT_with_file_path_and_lines_number_or_bytes
    data = COMMAND_OUTPUT_with_file_path_and_lines_number_or_bytes
    result = COMMAND_RESULT_with_file_path_and_lines_number_or_bytes
    return data, result


@pytest.fixture
def command_output_and_expected_result_with_path():
    from moler.cmd.unix.grep import COMMAND_OUTPUT_with_file_path, COMMAND_RESULT_with_file_path
    data = COMMAND_OUTPUT_with_file_path
    result = COMMAND_RESULT_with_file_path
    return data, result


@pytest.fixture
def command_output_and_expected_result_with_lines_number_and_bytes():
    from moler.cmd.unix.grep import COMMAND_OUTPUT_with_lines_number_and_bytes, \
        COMMAND_RESULT_with_lines_number_and_bytes
    data = COMMAND_OUTPUT_with_lines_number_and_bytes
    result = COMMAND_RESULT_with_lines_number_and_bytes
    return data, result


@pytest.fixture
def command_output_and_expected_result_with_lines_number():
    from moler.cmd.unix.grep import COMMAND_OUTPUT_with_lines_number_or_bytes, COMMAND_RESULT_with_lines_number_or_bytes
    data = COMMAND_OUTPUT_with_lines_number_or_bytes
    result = COMMAND_RESULT_with_lines_number_or_bytes
    return data, result


@pytest.fixture
def command_output_and_expected_result():
    from moler.cmd.unix.grep import COMMAND_OUTPUT_ver_human, COMMAND_RESULT_ver_human
    data = COMMAND_OUTPUT_ver_human
    result = COMMAND_RESULT_ver_human
    return data, result
