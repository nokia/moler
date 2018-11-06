# -*- coding: utf-8 -*-
"""
Testing of tcpdump command.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
_email_ = 'julia.patacz@nokia.com'

from moler.cmd.unix.tcpdump import Tcpdump


def test_tcpdump_returns_proper_command_string(buffer_connection):
    tcpdump_cmd = Tcpdump(buffer_connection, options="-c 4 -vv")
    assert "tcpdump -c 4 -vv" == tcpdump_cmd.command_string
