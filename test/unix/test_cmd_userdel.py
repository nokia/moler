# -*- coding: utf-8 -*-
"""
Userdel test module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import pytest

from moler.exceptions import CommandFailure
from moler.cmd.unix.userdel import Userdel


def test_userdel_returns_proper_command_string(buffer_connection):
    useradd_cmd = Userdel(buffer_connection, user='xyz', prompt=None, new_line_chars=None)
    assert "useradd xyz" == useradd_cmd.command_string
