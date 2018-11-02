# -*- coding: utf-8 -*-
"""
Testing of sudo command.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.cmd.unix.sudo import Sudo
from moler.cmd.unix.pwd import Pwd
from moler.exceptions import CommandTimeout
import pytest


def test_calling_by_command_object(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])

    cmd_pwd = Pwd(connection=buffer_connection.moler_connection)
    cmd_sudo = Sudo(connection=buffer_connection.moler_connection, sudo_password="pass", cmd_object=cmd_pwd)
    assert "sudo pwd" == cmd_sudo.command_string
    result = cmd_sudo()
    assert result == expected_result


def test_failing_with_timeout(buffer_connection, command_output_and_expected_result_timeout):
    command_output, expected_result = command_output_and_expected_result_timeout
    buffer_connection.remote_inject_response([command_output])
    cmd_pwd = Pwd(connection=buffer_connection.moler_connection)
    cmd_sudo = Sudo(connection=buffer_connection.moler_connection, sudo_password="pass", cmd_object=cmd_pwd)
    with pytest.raises(CommandTimeout):
        cmd_sudo(timeout=0.1)



@pytest.fixture()
def command_output_and_expected_result():
    output = """user@client:~/moler$ sudo pwd
[sudo] password for user: 
/home/user/moler
ute@debdev:~/moler$ """
    result = {"cmd_ret": {
        'current_path': 'moler',
        'full_path': '/home/user/moler',
        'path_to_current': '/home/user'
    }}
    return output, result


@pytest.fixture()
def command_output_and_expected_result_timeout():
    output = """user@client:~/moler$ sudo pwd
[sudo] password for user: 
/home/user/moler
"""
    result = {"cmd_ret": {
        'current_path': 'moler',
        'full_path': '/home/user/moler',
        'path_to_current': '/home/user'
    }}
    return output, result
