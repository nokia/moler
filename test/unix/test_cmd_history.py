# -*- coding: utf-8 -*-
"""
Testing of history command.
"""

__author__ = 'Marcin Szlapa'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.szlapa@nokia.com'

from moler.cmd.unix.history import History


def test_history_returns_proper_command_string(buffer_connection):
    history_cmd = History(buffer_connection)
    assert "history" == history_cmd.command_string
