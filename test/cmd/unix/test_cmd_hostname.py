# -*- coding: utf-8 -*-
"""
Testing of hostname command.
"""

__author__ = 'Cun Deng'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'cun.deng@nokia-sbell.com'


def test_hostname_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.hostname import Hostname
    hostname_cmd = Hostname(buffer_connection, options="-s")
    assert "hostname -s" == hostname_cmd.command_string

