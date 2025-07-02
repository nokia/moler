# -*- coding: utf-8 -*-
"""
Testing of hostnamectl command.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2025, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
from moler.exceptions import CommandFailure


def test_hostnamectl_wrong_parameter(buffer_connection, command_output_wrong_parameter):
    from moler.cmd.unix.hostnamectl import Hostnamectl
    buffer_connection.remote_inject_response([command_output_wrong_parameter])
    cmd = Hostnamectl(connection=buffer_connection.moler_connection, options="wrong-parameter val")
    with pytest.raises(CommandFailure):
        cmd()


def test_hostnamectl_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.hostnamectl import Hostnamectl
    cmd = Hostnamectl(buffer_connection, options="hostname newhostname")
    assert "hostnamectl hostname newhostname" == cmd.command_string


@pytest.fixture
def command_output_wrong_parameter():
    data = """hostnamectl wrong-parameter val
Unknown command verb wrong-parameter.
host:~ # """
    return data
