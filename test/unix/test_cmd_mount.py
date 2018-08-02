# -*- coding: utf-8 -*-
"""
Mount command test module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'

import pytest
from moler.cmd.unix.mount import Mount


def test_mount_returns_proper_command_string(buffer_connection):
    mount_cmd = Mount(connection=buffer_connection.moler_connection)
    assert "mount" == mount_cmd.command_string