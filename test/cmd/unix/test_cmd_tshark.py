# -*- coding: utf-8 -*-
"""
Testing of tshark command.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
_email_ = 'julia.patacz@nokia.com'

from moler.cmd.unix.tshark import Tshark


def test_tshark_returns_proper_command_string(buffer_connection):
    tshark_cmd = Tshark(buffer_connection, options="-a duration:10")
    assert "tshark -a duration:10" == tshark_cmd.command_string
