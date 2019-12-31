# -*- coding: utf-8 -*-
"""
Testing of route command.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
_email_ = 'julia.patacz@nokia.com'

import pytest

from moler.cmd.unix.route import Route
from moler.exceptions import CommandFailure


def test_route_returns_proper_command_string(buffer_connection):
    route_cmd = Route(buffer_connection)
    assert "route" == route_cmd.command_string


def test_calling_route_returns_result_file_exists(buffer_connection, command_output_and_expected_result_file_exists):
    command_output, expected_result_no_permit = command_output_and_expected_result_file_exists
    buffer_connection.remote_inject_response([command_output])
    route_cmd = Route(connection=buffer_connection.moler_connection,
                      options="add -net 0.0.0.0 netmask 0.0.0.0 gw 10.0.2.2")
    with pytest.raises(CommandFailure):
        route_cmd()


def test_calling_route_returns_result_no_such_file(buffer_connection,
                                                   command_output_and_expected_result_no_such_device):
    command_output, expected_result_no_permit = command_output_and_expected_result_no_such_device
    buffer_connection.remote_inject_response([command_output])
    route_cmd = Route(connection=buffer_connection.moler_connection, options="add -net 0.0.0.0 netmask 0.0.0.0")
    with pytest.raises(CommandFailure, match=r"Command failed in line 'SIOCADDRT: No such device'"):
        route_cmd()


def test_calling_route_returns_result_no_such_process(buffer_connection,
                                                      command_output_and_expected_result_no_such_process):
    command_output, expected_result_no_permit = command_output_and_expected_result_no_such_process
    buffer_connection.remote_inject_response([command_output])
    route_cmd = Route(connection=buffer_connection.moler_connection,
                      options="del -net 0.0.0.0 netmask 0.0.0.0 gw 10.0.2.2 metric 0")
    with pytest.raises(CommandFailure, match=r"Command failed in line 'SIOCDELRT: No such process'"):
        route_cmd()


@pytest.fixture
def command_output_and_expected_result_no_such_device():
    data = """
root@debdev:/home/ute# route add -net 0.0.0.0 netmask 0.0.0.0 
SIOCADDRT: No such device
root@debdev:/home/ute# """
    result = {}
    return data, result


@pytest.fixture
def command_output_and_expected_result_file_exists():
    data = """
root@debdev:/home/ute# route add -net 0.0.0.0 netmask 0.0.0.0 gw 10.0.2.2
SIOCADDRT: File exists
root@debdev:/home/ute# """
    result = {}
    return data, result


@pytest.fixture
def command_output_and_expected_result_no_such_process():
    data = """
root@debdev:/home/ute# route del -net 0.0.0.0 netmask 0.0.0.0 gw 10.0.2.2 metric 0
SIOCDELRT: No such process
root@debdev:/home/ute# """
    result = {}
    return data, result
