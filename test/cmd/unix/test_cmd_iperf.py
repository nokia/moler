# -*- coding: utf-8 -*-
"""
Iperf command test module.
"""

__author__ = 'Adrianna Pienkowska'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com'

import pytest
from moler.cmd.unix.iperf import Iperf
from moler.exceptions import CommandFailure


def test_iperf_returns_proper_command_string(buffer_connection):
     iperf_cmd = Iperf(buffer_connection, options='-c 10.1.1.1 -M 1300 -m')
     assert "iperf -c 10.1.1.1 -M 1300 -m" == iperf_cmd.command_string


def test_iperf_raise_error_on_bind_failed(buffer_connection, command_output_and_expected_result_on_bind_failed):
    iperf_cmd = Iperf(connection=buffer_connection.moler_connection, options='-s')
    command_output, expected_result = command_output_and_expected_result_on_bind_failed
    buffer_connection.remote_inject_response([command_output])
    assert 'iperf -s' == iperf_cmd.command_string
    with pytest.raises(CommandFailure):
        iperf_cmd()


def test_iperf_raise_error_on_no_such_file(buffer_connection, command_output_and_expected_result_on_connect_failed):
    iperf_cmd = Iperf(connection=buffer_connection.moler_connection, options='-c 10.156.236.132')
    command_output, expected_result = command_output_and_expected_result_on_connect_failed
    buffer_connection.remote_inject_response([command_output])
    assert 'iperf -c 10.156.236.132' == iperf_cmd.command_string
    with pytest.raises(CommandFailure):
        iperf_cmd()


def test_iperf_raise_error_on_iperf_problem(buffer_connection, command_output_and_expected_result_on_iperf_problem):
    iperf_cmd = Iperf(connection=buffer_connection.moler_connection, options='-i')
    command_output, expected_result = command_output_and_expected_result_on_iperf_problem
    buffer_connection.remote_inject_response([command_output])
    assert 'iperf -i' == iperf_cmd.command_string
    with pytest.raises(CommandFailure):
        iperf_cmd()


def test_iperf_correctly_parses_bidirectional_udp_client_output(buffer_connection):
    from moler.cmd.unix import iperf
    buffer_connection.remote_inject_response([iperf.COMMAND_OUTPUT_bidirectional_udp_client])
    iperf_cmd = iperf.Iperf(connection=buffer_connection.moler_connection,
                            **iperf.COMMAND_KWARGS_bidirectional_udp_client)
    res = iperf_cmd()
    assert res == iperf.COMMAND_RESULT_bidirectional_udp_client


def test_iperf_correctly_parses_bidirectional_udp_server_output(buffer_connection):
    from moler.cmd.unix import iperf
    buffer_connection.remote_inject_response([iperf.COMMAND_OUTPUT_bidirectional_udp_server])
    iperf_cmd = iperf.Iperf(connection=buffer_connection.moler_connection,
                            **iperf.COMMAND_KWARGS_bidirectional_udp_server)
    res = iperf_cmd()
    assert res == iperf.COMMAND_RESULT_bidirectional_udp_server


def test_iperf_correctly_parses_basic_udp_server_output(buffer_connection):
    from moler.cmd.unix import iperf
    buffer_connection.remote_inject_response([iperf.COMMAND_OUTPUT_basic_server])
    iperf_cmd = iperf.Iperf(connection=buffer_connection.moler_connection,
                            **iperf.COMMAND_KWARGS_basic_server)

    assert iperf_cmd() == iperf.COMMAND_RESULT_basic_server


def test_iperf_correctly_parses_basic_tcp_client_output(buffer_connection):
    from moler.cmd.unix import iperf
    buffer_connection.remote_inject_response([iperf.COMMAND_OUTPUT_basic_client])
    iperf_cmd = iperf.Iperf(connection=buffer_connection.moler_connection,
                            **iperf.COMMAND_KWARGS_basic_client)

    assert iperf_cmd() == iperf.COMMAND_RESULT_basic_client


def test_iperf_correctly_parses_multiconnection_tcp_client_output(buffer_connection):
    from moler.cmd.unix import iperf
    buffer_connection.remote_inject_response([iperf.COMMAND_OUTPUT_multiple_connections])
    iperf_cmd = iperf.Iperf(connection=buffer_connection.moler_connection,
                            **iperf.COMMAND_KWARGS_multiple_connections)

    assert iperf_cmd() == iperf.COMMAND_RESULT_multiple_connections


@pytest.fixture
def command_output_and_expected_result_on_bind_failed():
    output = """xyz@debian>iperf -s
bind failed: Address already in use
xyz@debian>"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_on_connect_failed():
    output = """xyz@debian>iperf -c 10.156.236.132
connect failed: Connection refused
xyz@debian>"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_on_iperf_problem():
    output = """xyz@debian>iperf -i
iperf: option requires an argument -- i 
xyz@debian>"""
    result = dict()
    return output, result

