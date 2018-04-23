# -*- coding: utf-8 -*-
"""
Testing of id command.
"""
__email__ = 'michal.ernst@nokia.com'


def test_id_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.id import Id
    id_cmd = Id(connection=buffer_connection.moler_connection, user="user")
    assert "id user" == id_cmd.command_string
