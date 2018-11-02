# -*- coding: utf-8 -*-
"""
Testing of sudo command.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.cmd.unix.sudo import Sudo
from moler.cmd.unix.pwd import Pwd
from moler.cmd.unix.cp import Cp
from moler.exceptions import CommandTimeout
from moler.exceptions import CommandFailure
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


def test_command_not_found(buffer_connection, command_output_command_not_found):
    command_output = command_output_command_not_found
    buffer_connection.remote_inject_response([command_output])
    cmd_pwd = Pwd(connection=buffer_connection.moler_connection)
    cmd_sudo = Sudo(connection=buffer_connection.moler_connection, sudo_password="pass", cmd_object=cmd_pwd)
    with pytest.raises(CommandFailure):
        cmd_sudo()


def test_no_parameters(buffer_connection):
    cmd_sudo = Sudo(connection=buffer_connection.moler_connection, sudo_password="pass")
    with pytest.raises(CommandFailure):
        cmd_sudo()


def test_failing_with_embedded_command_fails(buffer_connection, command_output_cp_fails):
    command_output = command_output_cp_fails
    buffer_connection.remote_inject_response([command_output])
    cmd_cp = Cp(connection=buffer_connection.moler_connection, src="src.txt", dst="dst.txt")
    cmd_sudo = Sudo(connection=buffer_connection.moler_connection, sudo_password="pass", cmd_object=cmd_cp)
    with pytest.raises(CommandFailure):
        cmd_sudo()


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


@pytest.fixture()
def command_output_cp_fails():
    output = """sudo cp src.txt dst.txt
[sudo] password for user: 
cp: cannot access
ute@debdev:~/moler$ """
    return output


@pytest.fixture()
def command_output_command_not_found():
    output = """sudo pwd
[sudo] password for ute: 
sudo: pwd: command not found
ute@debdev:~/moler$ """
    return output
