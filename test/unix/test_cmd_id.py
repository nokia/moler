# -*- coding: utf-8 -*-
"""
Testing of id command.
"""
__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import pytest


def test_id_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.id import Id
    id_cmd = Id(connection=buffer_connection.moler_connection, user="user")
    assert "id user" == id_cmd.command_string


def test_calling_id_returns_result_parsed_from_command_output(buffer_connection):
    from moler.cmd.unix.id import Id
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    cd_cmd = Id(connection=buffer_connection.moler_connection, user="user")
    result = cd_cmd()
    assert result == expected_result


@pytest.fixture
def command_output_and_expected_result():
    from moler.cmd.unix.id import COMMAND_OUTPUT_ver_execute as data
    from moler.cmd.unix.id import COMMAND_RESULT_ver_execute as result

    return data, result
