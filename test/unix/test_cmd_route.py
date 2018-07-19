# -*- coding: utf-8 -*-
"""
Testing of route command.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
_email_ = 'julia.patacz@nokia.com'

from moler.cmd.unix.route import Route


def test_route_returns_proper_command_string(buffer_connection):
    route_cmd = Route(buffer_connection)
    assert "route" == route_cmd.command_string
