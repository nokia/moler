# -*- coding: utf-8 -*-
"""
Testing of find command.
"""
__author__ = 'Adrianna Pienkowska '
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com'


from moler.exceptions import CommandFailure
from moler.cmd.unix.find import Find
import pytest


def test_find_returns_proper_command_string(buffer_connection):
    find_cmd = Find(connection=buffer_connection.moler_connection, files=['sed', 'uname'], real_options='-H')
    assert "find -H sed uname" == find_cmd.command_string
