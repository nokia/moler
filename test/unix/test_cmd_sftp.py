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
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host="myhost.com", prompt=None, new_line_chars=None)
    assert "sftp myhost.com" == sftp_cmd.command_string


def test_sftp_returns_proper_command_string_user(buffer_connection):
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host="myhost.com", user="fred",
                    prompt=None, new_line_chars=None)
    assert "sftp fred@myhost.com" == sftp_cmd.command_string


def test_sftp_returns_proper_command_string_pathname(buffer_connection):
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host="myhost.com", user="fred",
                    pathname="/home/fred/homework.txt", prompt=None, new_line_chars=None)
    assert "sftp fred@myhost.com:/home/fred/homework.txt" == sftp_cmd.command_string


def test_sftp_returns_proper_command_string_new_pathname(buffer_connection):
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host="myhost.com", user="fred",
                    pathname="/home/fred/homework.txt", new_pathname="/home/vivi/new_homework.txt", prompt=None,
                    new_line_chars=None)
    assert "sftp fred@myhost.com:/home/fred/homework.txt /home/vivi/new_homework.txt" == sftp_cmd.command_string

