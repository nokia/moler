# -*- coding: utf-8 -*-
"""
Iperf3 command test module.
"""

__author__ = "Kacper Kozik"
__copyright__ = "Copyright (C) 2023, Nokia"
__email__ = "kacper.kozik@nokia.com"

import pytest
import mock
from moler.cmd.unix.iperf3 import Iperf3
from moler.exceptions import CommandFailure


def test_iperf_returns_proper_command_string(buffer_connection):
    iperf_cmd = Iperf3(buffer_connection, options='-c 10.1.1.1 -M 1300 -m')
    assert "iperf3 -c 10.1.1.1 -M 1300 -m" == iperf_cmd.command_string


# def test_iperf_can_set_direct_path_to_command_executable(buffer_connection):
#     iperf_cmd = Iperf3(buffer_connection, options='-c 10.1.1.1 -M 1300 -m')
#     assert "iperf3 -c 10.1.1.1 -M 1300 -m" == iperf_cmd.command_string
#     iperf_cmd.command_path = 'adb shell /data/data/com.magicandroidapps.iperf/bin/'
#     assert "adb shell /data/data/com.magicandroidapps.iperf/bin/iperf -c 10.1.1.1 -M 1300 -m" == iperf_cmd.command_string


def test_iperf_raise_error_on_bind_failed(buffer_connection, command_output_and_expected_result_on_bind_failed):
    iperf_cmd = Iperf3(
        connection=buffer_connection.moler_connection, options='-s')
    command_output, expected_result = command_output_and_expected_result_on_bind_failed
    buffer_connection.remote_inject_response([command_output])
    assert 'iperf3 -s' == iperf_cmd.command_string
    with pytest.raises(CommandFailure):
        iperf_cmd()


def test_iperf_raise_error_on_no_such_file(buffer_connection, command_output_and_expected_result_on_connect_failed):
    iperf_cmd = Iperf3(
        connection=buffer_connection.moler_connection, options='-c 10.156.236.132')
    command_output, expected_result = command_output_and_expected_result_on_connect_failed
    buffer_connection.remote_inject_response([command_output])
    assert 'iperf3 -c 10.156.236.132' == iperf_cmd.command_string
    with pytest.raises(CommandFailure):
        iperf_cmd()


def test_iperf_raise_error_on_iperf_problem(buffer_connection, command_output_and_expected_result_on_iperf_problem):
    iperf_cmd = Iperf3(
        connection=buffer_connection.moler_connection, options='-i')
    command_output, expected_result = command_output_and_expected_result_on_iperf_problem
    buffer_connection.remote_inject_response([command_output])
    assert 'iperf3 -i' == iperf_cmd.command_string
    with pytest.raises(CommandFailure):
        iperf_cmd()


# def test_iperf_raise_error_on_iperf_problem(buffer_connection):
#     with pytest.raises(AttributeError) as err:
#         Iperf2(connection=buffer_connection.moler_connection, options='-d -P 10')
#     assert "Unsupported options combination (--dualtest & --parallel)" in str(
#         err.value)


# def test_iperf_stores_connections_as_host_port_tuple_for_local_and_remote(buffer_connection):
#     from moler.cmd.unix import iperf3
#     buffer_connection.remote_inject_response(
#         [iperf3.COMMAND_OUTPUT_bidirectional_udp_server])
#     iperf_cmd = iperf3.Iperf3(connection=buffer_connection.moler_connection,
#                               **iperf3.COMMAND_KWARGS_bidirectional_udp_server)
#     iperf_cmd()
#     stored_connections = iperf_cmd.result()['CONNECTIONS'].keys()
#     #      local port@host      remote port@host
#     assert len(stored_connections) == 4
#     assert ('56262@192.168.0.10', '5016@192.168.0.12') in stored_connections
#     assert ('47384@192.168.0.12', '5016@192.168.0.10') in stored_connections
#     assert ('192.168.0.10', '5016@192.168.0.12') in stored_connections
#     assert ('192.168.0.12', '5016@192.168.0.10') in stored_connections


# def test_iperf_stores_connections_as_port_at_host_tuple_for_local_and_remote(buffer_connection):
#     from moler.cmd.unix import iperf2
#     buffer_connection.remote_inject_response(
#         [iperf2.COMMAND_OUTPUT_bidirectional_udp_server])
#     iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
#                               **iperf2.COMMAND_KWARGS_bidirectional_udp_server)
#     iperf_cmd()
#     stored_connections = iperf_cmd.result()['CONNECTIONS'].keys()
#     #        local host:port      remote host:port
#     assert len(stored_connections) == 4
#     assert ('56262@192.168.0.10', '5016@192.168.0.12') in stored_connections
#     assert ('47384@192.168.0.12', '5016@192.168.0.10') in stored_connections
#     assert ('192.168.0.10', '5016@192.168.0.12') in stored_connections
#     assert ('192.168.0.12', '5016@192.168.0.10') in stored_connections


def test_iperf_stores_ipv6_connections_as_port_at_host_tuple_for_local_and_remote(buffer_connection):
    from moler.cmd.unix import iperf3
    buffer_connection.remote_inject_response(
        [iperf3.COMMAND_OUTPUT_tcp_ipv6_client])
    iperf_cmd = iperf3.Iperf3(connection=buffer_connection.moler_connection,
                              **iperf3.COMMAND_KWARGS_tcp_ipv6_client)
    iperf_cmd()
    stored_connections = iperf_cmd.result()['CONNECTIONS'].keys()
    #      local port@host      remote port@host
    assert len(stored_connections) == 2
    assert ("49597@fd00::2:0", "5901@fd00::1:0") in stored_connections
    assert ("fd00::2:0", "5901@fd00::1:0") in stored_connections


def test_iperf_creates_summary_connection_for_parallel_testing(buffer_connection):
    from moler.cmd.unix import iperf3
    buffer_connection.remote_inject_response(
        [iperf3.COMMAND_OUTPUT_multiple_connections])
    iperf_cmd = iperf3.Iperf3(connection=buffer_connection.moler_connection,
                              **iperf3.COMMAND_KWARGS_multiple_connections)
    iperf_cmd()
    stored_connections = iperf_cmd.result()['CONNECTIONS'].keys()
    #        local host:port      remote host:port
    assert len(stored_connections) == 5
    assert ('multiport@127.0.0.1',
            '5201@127.0.0.1') in stored_connections  # summary
    assert ('127.0.0.1', '5201@127.0.0.1') in stored_connections  # result


@pytest.fixture
def command_output_and_expected_result_on_bind_failed():
    output = """xyz@debian>iperf3 -s
bind failed: Address already in use
xyz@debian>"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_on_connect_failed():
    output = """xyz@debian>iperf3 -c 10.156.236.132
connect failed: Connection refused
xyz@debian>"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_on_iperf_problem():
    output = """xyz@debian>iperf3 -i
iperf: option requires an argument -- i 
xyz@debian>"""
    result = dict()
    return output, result
