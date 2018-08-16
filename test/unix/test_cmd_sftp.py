# -*- coding: utf-8 -*-
"""
SFTP command test module.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


# import pytest
from moler.cmd.unix.sftp import Sftp


def test_sftp_returns_proper_command_string(buffer_connection):
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, prompt=None, new_line_chars=None)
    assert "sftp" == sftp_cmd.command_string
