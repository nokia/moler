# -*- coding: utf-8 -*-
"""
Iperf2 command test module.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import pytest
import mock
from moler.cmd.unix.iperf2 import Iperf2
from moler.exceptions import CommandFailure


def test_iperf_returns_proper_command_string(buffer_connection):
     iperf_cmd = Iperf2(buffer_connection, options='-c 10.1.1.1 -M 1300 -m')
     assert "iperf -c 10.1.1.1 -M 1300 -m" == iperf_cmd.command_string


def test_iperf_raise_error_on_bind_failed(buffer_connection, command_output_and_expected_result_on_bind_failed):
    iperf_cmd = Iperf2(connection=buffer_connection.moler_connection, options='-s')
    command_output, expected_result = command_output_and_expected_result_on_bind_failed
    buffer_connection.remote_inject_response([command_output])
    assert 'iperf -s' == iperf_cmd.command_string
    with pytest.raises(CommandFailure):
        iperf_cmd()


def test_iperf_raise_error_on_no_such_file(buffer_connection, command_output_and_expected_result_on_connect_failed):
    iperf_cmd = Iperf2(connection=buffer_connection.moler_connection, options='-c 10.156.236.132')
    command_output, expected_result = command_output_and_expected_result_on_connect_failed
    buffer_connection.remote_inject_response([command_output])
    assert 'iperf -c 10.156.236.132' == iperf_cmd.command_string
    with pytest.raises(CommandFailure):
        iperf_cmd()


def test_iperf_raise_error_on_iperf_problem(buffer_connection, command_output_and_expected_result_on_iperf_problem):
    iperf_cmd = Iperf2(connection=buffer_connection.moler_connection, options='-i')
    command_output, expected_result = command_output_and_expected_result_on_iperf_problem
    buffer_connection.remote_inject_response([command_output])
    assert 'iperf -i' == iperf_cmd.command_string
    with pytest.raises(CommandFailure):
        iperf_cmd()


def test_iperf_raise_error_on_iperf_problem(buffer_connection):
    with pytest.raises(AttributeError) as err:
        Iperf2(connection=buffer_connection.moler_connection, options='-d -P 10')
    assert "Unsupported options combination (--dualtest & --parallel)" in str(err.value)


def test_iperf_stores_connections_as_host_port_tuple_for_local_and_remote(buffer_connection):
    from moler.cmd.unix import iperf2
    buffer_connection.remote_inject_response([iperf2.COMMAND_OUTPUT_bidirectional_udp_server])
    iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
                              **iperf2.COMMAND_KWARGS_bidirectional_udp_server)
    iperf_cmd()
    stored_connections = iperf_cmd.result()['CONNECTIONS'].keys()
    #        local host:port      remote host:port
    assert len(stored_connections) == 4
    assert ('192.168.0.10:56262', '192.168.0.12:5016') in stored_connections
    assert ('192.168.0.12:47384', '192.168.0.10:5016') in stored_connections
    assert ('192.168.0.10', '192.168.0.12:5016') in stored_connections
    assert ('192.168.0.12', '192.168.0.10:5016') in stored_connections


def test_iperf_creates_summary_connection_for_parallel_testing(buffer_connection):
    from moler.cmd.unix import iperf2
    buffer_connection.remote_inject_response([iperf2.COMMAND_OUTPUT_multiple_connections])
    iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
                              **iperf2.COMMAND_KWARGS_multiple_connections)
    iperf_cmd()
    stored_connections = iperf_cmd.result()['CONNECTIONS'].keys()
    #        local host:port      remote host:port
    assert len(stored_connections) == 22
    assert ('192.168.0.102:multiport', '192.168.0.100:5001') in stored_connections  # summary
    assert ('192.168.0.102', '192.168.0.100:5001') in stored_connections  # result


def test_iperf_correctly_parses_bidirectional_udp_client_output(buffer_connection):
    from moler.cmd.unix import iperf2
    buffer_connection.remote_inject_response([iperf2.COMMAND_OUTPUT_bidirectional_udp_client])
    iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
                              **iperf2.COMMAND_KWARGS_bidirectional_udp_client)
    res = iperf_cmd()
    assert res == iperf2.COMMAND_RESULT_bidirectional_udp_client


def test_iperf_correctly_parses_bidirectional_udp_server_output(buffer_connection):
    from moler.cmd.unix import iperf2
    buffer_connection.remote_inject_response([iperf2.COMMAND_OUTPUT_bidirectional_udp_server])
    iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
                              **iperf2.COMMAND_KWARGS_bidirectional_udp_server)
    res = iperf_cmd()
    assert res == iperf2.COMMAND_RESULT_bidirectional_udp_server


def test_iperf_correctly_parses_basic_udp_server_output(buffer_connection):
    from moler.cmd.unix import iperf2
    buffer_connection.remote_inject_response([iperf2.COMMAND_OUTPUT_basic_server])
    iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
                              **iperf2.COMMAND_KWARGS_basic_server)
    ret = iperf_cmd()
    assert ret == iperf2.COMMAND_RESULT_basic_server


def test_iperf_correctly_parses_basic_tcp_client_output(buffer_connection):
    from moler.cmd.unix import iperf2
    buffer_connection.remote_inject_response([iperf2.COMMAND_OUTPUT_basic_client])
    iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
                              **iperf2.COMMAND_KWARGS_basic_client)
    res = iperf_cmd()
    assert res == iperf2.COMMAND_RESULT_basic_client


def test_iperf_correctly_parses_multiconnection_tcp_client_output(buffer_connection):
    from moler.cmd.unix import iperf2
    buffer_connection.remote_inject_response([iperf2.COMMAND_OUTPUT_multiple_connections])
    iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
                              **iperf2.COMMAND_KWARGS_multiple_connections)
    ret = iperf_cmd()
    assert ret == iperf2.COMMAND_RESULT_multiple_connections


def test_iperf_correctly_parses_multiconnection_tcp_server_output(buffer_connection):
    from moler.cmd.unix import iperf2
    buffer_connection.remote_inject_response([iperf2.COMMAND_OUTPUT_multiple_connections_server])
    iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
                              **iperf2.COMMAND_KWARGS_multiple_connections_server)
    ret = iperf_cmd()
    assert ret == iperf2.COMMAND_RESULT_multiple_connections_server


def test_iperf_detecting_dualtest_at_client(buffer_connection):
    from moler.cmd.unix import iperf2
    iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
                              **iperf2.COMMAND_KWARGS_bidirectional_udp_client)
    assert iperf_cmd.works_in_dualtest is True
    iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
                              **iperf2.COMMAND_KWARGS_basic_client)
    assert iperf_cmd.works_in_dualtest is False


def test_iperf_detecting_dualtest_at_server(buffer_connection):
    from moler.cmd.unix import iperf2

    buffer_connection.remote_inject_response([iperf2.COMMAND_OUTPUT_bidirectional_udp_server])
    iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
                              **iperf2.COMMAND_KWARGS_bidirectional_udp_server)
    iperf_cmd()
    assert iperf_cmd.works_in_dualtest is True

    buffer_connection.remote_inject_response([iperf2.COMMAND_OUTPUT_multiple_connections_server])
    iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
                              **iperf2.COMMAND_KWARGS_multiple_connections_server)
    iperf_cmd()
    assert iperf_cmd.works_in_dualtest is False


def test_iperf_sends_additional_ctrl_c_after_detecting_to_early_ctrl_c(buffer_connection):
    from moler.cmd.unix import iperf2

    normal_iperf_output = iperf2.COMMAND_OUTPUT_multiple_connections_server.splitlines(True)
    last_line_with_prompt = normal_iperf_output[-1]
    normal_iperf_output[-1] = "^CWaiting for server threads to complete. Interrupt again to force quit\n"
    normal_iperf_output.append(last_line_with_prompt)
    output_with_too_early_ctrl_c = "".join(normal_iperf_output)

    buffer_connection.remote_inject_response([output_with_too_early_ctrl_c])
    iperf_cmd = iperf2.Iperf2(connection=buffer_connection.moler_connection,
                              **iperf2.COMMAND_KWARGS_multiple_connections_server)
    with mock.patch.object(iperf_cmd, "_stop_server"):
        with mock.patch.object(iperf_cmd, "break_cmd") as break_cmd_method:
            iperf_cmd()
    break_cmd_method.assert_called_once_with()


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

