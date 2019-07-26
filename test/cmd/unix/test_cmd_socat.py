# -*- coding: utf-8 -*-
"""
Socat command test module.
"""

__author__ = 'Adrianna Pienkowska, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com, marcin.usielski@nokia.com'

import pytest
from moler.cmd.unix.socat import Socat
from moler.exceptions import CommandFailure


def test_socat_returns_proper_command_string(buffer_connection):
    socat_cmd = Socat(connection=buffer_connection.moler_connection, input_options='TCP4-LISTEN:1234,reuseaddr,fork',
                      output_options='gopen:/home/capture,seek-end=,append')
    assert "socat TCP4-LISTEN:1234,reuseaddr,fork gopen:/home/capture,seek-end=,append" == socat_cmd.command_string


def test_socat_raise_connection_refused(buffer_connection, command_output_and_expected_result_on_connection_refused):
    socat_cmd = Socat(connection=buffer_connection.moler_connection, input_options='STDIO',
                      output_options='tcp:localhost:3334', options='-d')
    command_output, expected_result = command_output_and_expected_result_on_connection_refused
    buffer_connection.remote_inject_response([command_output])
    assert 'socat -d STDIO tcp:localhost:3334' == socat_cmd.command_string
    with pytest.raises(CommandFailure):
        socat_cmd()


def test_socat_raise_device_unknown(buffer_connection, command_output_and_expected_result_on_device_unknown):
    socat_cmd = Socat(connection=buffer_connection.moler_connection,
                      input_options='READLINE,history=$HOME/.cmd_history', output_options='/dev/ttyS0,raw,echo=0,crnl')
    command_output, expected_result = command_output_and_expected_result_on_device_unknown
    buffer_connection.remote_inject_response([command_output])
    assert 'socat READLINE,history=$HOME/.cmd_history /dev/ttyS0,raw,echo=0,crnl' == socat_cmd.command_string
    with pytest.raises(CommandFailure):
        socat_cmd()


def test_socat_raise_address_required(buffer_connection, command_output_and_expected_result_on_address_required):
    socat_cmd = Socat(connection=buffer_connection.moler_connection)
    command_output, expected_result = command_output_and_expected_result_on_address_required
    buffer_connection.remote_inject_response([command_output])
    assert 'socat' == socat_cmd.command_string
    with pytest.raises(CommandFailure):
        socat_cmd()


@pytest.fixture
def command_output_and_expected_result_on_connection_refused():
    output = """xyz@debian> socat -d STDIO tcp:localhost:3334
2018/08/20 11:22:29 socat[31916] E connect(5, AF=2 127.0.0.1:3334, 16): Connection refused
xyz@debian>"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_on_device_unknown():
    output = """xyz@debian> socat READLINE,history=$HOME/.cmd_history /dev/ttyS0,raw,echo=0,crnl 
2018/08/20 12:57:05 socat[4296] E unknown device/address "READLINE"
xyz@debian>"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_on_address_required():
    output = """xyz@debian> socat READLINE,history=$HOME/.cmd_history /dev/ttyS0,raw,echo=0,crnl 
2018/08/20 12:57:05 socat[4296] E unknown device/address "READLINE"
xyz@debian>"""
    result = dict()
    return output, result
