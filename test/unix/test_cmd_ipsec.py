# -*- coding: utf-8 -*-
"""
Testing of ipsec command.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
_email_ = 'julia.patacz@nokia.com'

from moler.cmd.unix.ipsec import Ipsec


def test_ipsec_returns_proper_command_string(buffer_connection):
    ipsec_cmd = Ipsec(buffer_connection, options="statusall")
    assert "ipsec statusall" == ipsec_cmd.command_string
