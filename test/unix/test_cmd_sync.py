# -*- coding: utf-8 -*-
"""
Testing of sync command.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com'


def test_sync_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.sync import Sync
    sync_cmd = Sync(connection=buffer_connection.moler_connection)
    assert "sync" == sync_cmd.command_string
