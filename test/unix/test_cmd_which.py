# -*- coding: utf-8 -*-
"""
Which command test module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


from moler.cmd.unix.which import Which


def test_which_returns_proper_command_string(buffer_connection):
    which_cmd = Which(connection=buffer_connection.moler_connection, names=["uname", "git", "firefox"], prompt=None,
                      new_line_chars=None)
    assert "which uname git firefox" == which_cmd.command_string


def test_which_returns_proper_command_string_show_all(buffer_connection):
    which_cmd = Which(connection=buffer_connection.moler_connection, show_all=True, names=["man"],
                      prompt=None, new_line_chars=None)
    assert "which -a man" == which_cmd.command_string
