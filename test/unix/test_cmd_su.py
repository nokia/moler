# -*- coding: utf-8 -*-
"""
Su command module.
"""

__author__ = 'Agnieszka Bylica, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, marcin.usielski@nokia.com'

import pytest

from moler.cmd.unix.su import Su


def test_su_returns_proper_command_string(buffer_connection):
    telnet_cmd = Su(buffer_connection, login='xyz', options='-p', password="1234", prompt=None, newline_chars=None)
    assert "su -p xyz" == telnet_cmd.command_string


def test_su_catches_authentication_failure(buffer_connection, command_output_and_expected_result_auth):
    from moler.exceptions import CommandFailure
    command_output, expected_result = command_output_and_expected_result_auth
    buffer_connection.remote_inject_response([command_output])
    su_cmd = Su(connection=buffer_connection.moler_connection, prompt=r"xyz@debian:")
    with pytest.raises(CommandFailure):
        su_cmd()


def test_su_catches_command_format_failure(buffer_connection,
                                           command_output_and_expected_result_command_format_failure):
    from moler.exceptions import CommandFailure
    command_output, expected_result = command_output_and_expected_result_command_format_failure
    buffer_connection.remote_inject_response([command_output])
    su_cmd = Su(connection=buffer_connection.moler_connection)
    with pytest.raises(CommandFailure):
        su_cmd()


def test_su_catches_username_failure(buffer_connection, command_output_and_expected_result_username_failure):
    from moler.exceptions import CommandFailure
    command_output, expected_result = command_output_and_expected_result_username_failure
    buffer_connection.remote_inject_response([command_output])
    su_cmd = Su(connection=buffer_connection.moler_connection)
    with pytest.raises(CommandFailure):
        su_cmd()


@pytest.fixture
def command_output_and_expected_result_auth():
    output = """xyz@debian:~/Moler$ su
Password: 
su: Authentication failure
xyz@debian:~/Moler$"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_command_format_failure():
    output = """xyz@debian:~/Moler$ su -g 
su: invalid option -- 'g'
Usage: su [options] [LOGIN]

Options:
  -c, --command COMMAND         pass COMMAND to the invoked shell
  -h, --help                    display this help message and exit
  -, -l, --login                make the shell a login shell
  -m, -p,
  --preserve-environment        do not reset environment variables, and
                                keep the same shell
  -s, --shell SHELL             use SHELL instead of the default in passwd
xyz@debian:~/Moler$"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_username_failure():
    output = """xyz@debian:~/Moler$ su kla
No passwd entry for user 'kla'
xyz@debian:~/Moler$"""
    result = dict()
    return output, result
