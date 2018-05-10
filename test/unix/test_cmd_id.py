# -*- coding: utf-8 -*-
"""
Testing of id command.
"""
__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import pytest


def test_id_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.id import Id
    id_cmd = Id(connection=buffer_connection.moler_connection, user="user")
    assert "id user" == id_cmd.command_string
