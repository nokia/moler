# -*- coding: utf-8 -*-
"""
Testing of mpstat command.
"""
__author__ = 'Julia Patacz, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
_email_ = 'julia.patacz@nokia.com, marcin.usielski@nokia.com'

import pytest
from moler.cmd.unix.mpstat import Mpstat
from moler.exceptions import CommandFailure


def test_mpstat_returns_proper_command_string(buffer_connection):
    mpstat_cmd = Mpstat(buffer_connection, options="-P 0")
    assert "mpstat -P 0" == mpstat_cmd.command_string


def test_mpstat_wrong_value(buffer_connection):
    wrong_output = """
user@dev:~# mpstat
Linux 4.4.112-rt127 (type)    05/10/18    _armv7l_    (4 CPU)
11:07:06     CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest   %idle
11:07:06     all    WO     0.07      2.28   0.50    0.00    0.17    0.00    0.00   95.49
user@dev:~# """
    buffer_connection.remote_inject_response([wrong_output])
    cmd = Mpstat(buffer_connection)
    with pytest.raises(CommandFailure):
        cmd()
