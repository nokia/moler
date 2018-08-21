# -*- coding: utf-8 -*-
"""
Testing of ip link command.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
_email_ = 'julia.patacz@nokia.com'

from moler.cmd.unix.ip_link import IpLink


def test_ip_link_returns_proper_command_string(buffer_connection):
    ip_link_cmd = IpLink(buffer_connection, action="show", options="dev eth0")
    assert "ip link show dev eth0" == ip_link_cmd.command_string
