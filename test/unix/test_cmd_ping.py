# -*- coding: utf-8 -*-
"""
Testing of ping command.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
_email_ = 'julia.patacz@nokia.com'

import pytest

from moler.cmd.unix.ping import Ping


def test_ping_returns_proper_command_string(buffer_connection):
    ping_cmd = Ping(buffer_connection, destination="localhost", options="-c 5")
    assert "ping localhost -c 5" == ping_cmd.command_string

def test_ping_observer_timeout(buffer_connection):
    from moler.exceptions import CommandTimeout
    with pytest.raises(CommandTimeout):
        cmd_ping = Ping(buffer_connection.moler_connection, destination='localhost')
        cmd_ping()
