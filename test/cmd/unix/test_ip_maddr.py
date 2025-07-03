# -*- coding: utf-8 -*-
"""
Testing of hostnamectl command.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2025, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
from moler.exceptions import CommandFailure
from moler.cmd.unix.ip_maddr import IpMaddr


def test_ip_maddr_wrong_parameter(buffer_connection, command_output_wrong_parameter):

    buffer_connection.remote_inject_response([command_output_wrong_parameter])
    cmd = IpMaddr(connection=buffer_connection.moler_connection, options="wrong")
    with pytest.raises(CommandFailure):
        cmd()


def test_ip_maddr_returns_proper_command_string(buffer_connection):
    cmd = IpMaddr(buffer_connection, options="show")
    assert "ip maddr show" == cmd.command_string


@pytest.fixture
def command_output_wrong_parameter():
    data = """ip maddr wrong
Command "wrong" is unknown, try "ip maddr help".
host:~ # """
    return data
