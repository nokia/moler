# -*- coding: utf-8 -*-
"""
Testing of service command.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
_email_ = 'julia.patacz@nokia.com'

from moler.cmd.unix.service import Service


def test_service_returns_proper_command_string(buffer_connection):
    service_cmd = Service(buffer_connection, options="--status-all")
    assert "service --status-all" == service_cmd.command_string
