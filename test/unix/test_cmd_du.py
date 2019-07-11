# -*- coding: utf-8 -*-
"""
Testing of du command.
"""

__author__ = 'Marcin Szlapa'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.szlapa@nokia.com'

from moler.cmd.unix.du import Du


def test_du_returns_proper_command_string(buffer_connection):
    du_cmd = Du(buffer_connection, options="-sk *")
    assert "du -sk *" == du_cmd.command_string
