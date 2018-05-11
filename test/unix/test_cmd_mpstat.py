# -*- coding: utf-8 -*-
"""
Testing of mpstat command.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
_email_ = 'julia.patacz@nokia.com'

from moler.cmd.unix.mpstat import Mpstat


def test_mpstat_returns_proper_command_string(buffer_connection):
    mpstat_cmd = Mpstat(buffer_connection, options="-P 0")
    assert "mpstat -P 0" == mpstat_cmd.command_string
