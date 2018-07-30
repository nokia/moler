# -*- coding: utf-8 -*-
"""
Which command test module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import pytest

from moler.exceptions import CommandFailure
from moler.cmd.unix.which import Which


def test_which_returns_proper_command_string(buffer_connection):
    uname_cmd = Uname(connection=buffer_connection.moler_connection)
    assert "which" == uname_cmd.command_string