# -*- coding: utf-8 -*-
"""
Wget command test module.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


from moler.cmd.unix.wget import Wget
import pytest


def test_wget_returns_proper_command_string(buffer_connection):
    wget_cmd = Wget(connection=buffer_connection.moler_connection)
    assert "wget" == wget_cmd.command_string
