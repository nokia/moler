# -*- coding: utf-8 -*-
"""
Testing of ip route command.
"""
import pytest

__author__ = 'Yang Snackwell'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'snackwell.yang@nokia-sbell.com'


def test_calling_iproute_get_default_returns_result_parsed_from_command_output(buffer_connection,
                                                                               command_output_and_expected_result):
    from moler.cmd.unix.ip_route import Ip_route
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    iproute_cmd = Ip_route(connection=buffer_connection.moler_connection)
    iproute_cmd()
    result = iproute_cmd.get_default_route()
    expected_default_route = "10.83.207.254"
    assert result == expected_default_route


def test_iproute_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.ip_route import Ip_route
    iproute_cmd = Ip_route(buffer_connection, is_ipv6=True)
    assert "ip -6 route" == iproute_cmd.command_string


# --------------------------- resources


@pytest.fixture
def command_output_and_expected_result():
    from moler.cmd.unix.ip_route import COMMAND_OUTPUT_ver_human, COMMAND_RESULT_ver_human
    data = COMMAND_OUTPUT_ver_human
    result = COMMAND_RESULT_ver_human
    return data, result
