# -*- coding: utf-8 -*-
"""
Echo command test module.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'

import pytest
from moler.cmd.unix.echo import Echo


def test_echo_returns_proper_command_string(buffer_connection):
    echo_cmd = Echo(connection=buffer_connection.moler_connection)
    assert "echo" == echo_cmd.command_string
