# -*- coding: utf-8 -*-
"""
SFTP command test module.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import pytest
from moler.cmd.unix.sftp import Sftp
from moler.exceptions import CommandFailure


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


def test_sftp_raises_command_error(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_command()
    buffer_connection.remote_inject_response([command_output])
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host='192.168.0.102', user='fred', pathname='cat',
                    new_pathname='/home/xyz/Docs/cat', prompt=None, new_line_chars=None)
    with pytest.raises(CommandFailure):
        sftp_cmd()


def test_sftp_raises_file_error(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_file()
    buffer_connection.remote_inject_response([command_output])
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host='192.168.0.102', user='fred', pathname='dog',
                    new_pathname='/home/xyz/Docs/dog', prompt=None, new_line_chars=None)
    with pytest.raises(CommandFailure):
        sftp_cmd()


@pytest.fixture
def command_output_and_expected_result_command():
    data = """xyz@debian:/home$ sftp fred@192.168.0.102:cat /home/xyz/Docs/cat
fred@192.168.0.102's password: 
Permission denied, please try again.
fred@192.168.0.102's password: 
Permission denied, please try again.
fred@192.168.0.102's password: 
Permission denied (publickey,password).
Couldn't read packet: Connection reset by peer   
xyz@debian:/home$"""
    result = dict()
    return data, result


@pytest.fixture
def command_output_and_expected_result_file():
    data = """xyz@debian:/home$ sftp fred@192.168.0.102:dog /home/xyz/Docs/dog
fred@192.168.0.102's password: 
Connected to 192.168.0.102.
File "/upload/dog" not found.   
xyz@debian:/home$"""
    result = dict()
    return data, result
