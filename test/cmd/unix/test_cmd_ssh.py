# -*- coding: utf-8 -*-
"""
Testing of ssh command.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.cmd.unix.ssh import Ssh
from moler.exceptions import CommandFailure
from moler.exceptions import CommandTimeout
import pytest


def test_calling_ssh_returns_result_parsed_from_command_output(buffer_connection, command_output_and_expected_result):
    command_output = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])

    ssh_cmd = Ssh(connection=buffer_connection.moler_connection, login="user", password="english",
                  host="host.domain.net", expected_prompt="host:.*#", options=None)
    assert "TERM=xterm-mono ssh -l user host.domain.net" == ssh_cmd.command_string
    assert ssh_cmd() is not None


def test_ssh_failed_with_multiple_passwords(buffer_connection, command_output_2_passwords):
    command_output = command_output_2_passwords
    buffer_connection.remote_inject_response([command_output])

    ssh_cmd = Ssh(connection=buffer_connection.moler_connection, login="user", password="english",
                  host="host.domain.net", expected_prompt="host:.*#", prompt="starthost:~ >", repeat_password=False,
                  options=None)
    assert "TERM=xterm-mono ssh -l user host.domain.net" == ssh_cmd.command_string
    with pytest.raises(CommandFailure):
        ssh_cmd()


def test_ssh_failed_host_key_verification(buffer_connection, command_output_failed_host_key_verification):
    command_output = command_output_failed_host_key_verification
    buffer_connection.remote_inject_response([command_output])

    ssh_cmd = Ssh(connection=buffer_connection.moler_connection, login="user", password="english",
                  host="host.domain.net", expected_prompt="server:.*#", prompt="host:~ #", options=None)
    assert "TERM=xterm-mono ssh -l user host.domain.net" == ssh_cmd.command_string
    with pytest.raises(CommandFailure):
        ssh_cmd()


def test_ssh_username_and_login(buffer_connection):
    with pytest.raises(CommandFailure) as ex:
        Ssh(connection=buffer_connection.moler_connection, login="user", password="english", port=1500,
            host="host.domain.net", expected_prompt=r"host:.*#", prompt=r"user@client.*>",
            username="username")
    assert "not both" in str(ex)
    assert "Ssh" in str(ex)


def test_ssh_failed_permission_denied(buffer_connection, command_output_permission_denied):
    command_output = command_output_permission_denied
    buffer_connection.remote_inject_response([command_output])

    ssh_cmd = Ssh(connection=buffer_connection.moler_connection, login="user", password="english",
                  host="host.domain.net", expected_prompt="host:.*#", options=None)
    assert "TERM=xterm-mono ssh -l user host.domain.net" == ssh_cmd.command_string
    with pytest.raises(CommandFailure):
        ssh_cmd()


def test_ssh_failed_permission_denied_key_pass_keyboard(buffer_connection, command_output_permission_denied_key):
    command_output = command_output_permission_denied_key
    buffer_connection.remote_inject_response([command_output])

    ssh_cmd = Ssh(connection=buffer_connection.moler_connection, login="user", password="english",
                  host="host.domain.net", expected_prompt="host:.*#", options=None,
                  permission_denied_key_pass_keyboard=None)
    assert "TERM=xterm-mono ssh -l user host.domain.net" == ssh_cmd.command_string
    with pytest.raises(CommandFailure):
        ssh_cmd()


def test_ssh_failed_known_hosts(buffer_connection, command_output_failed_known_hosts):
    command_output = command_output_failed_known_hosts
    buffer_connection.remote_inject_response([command_output])

    ssh_cmd = Ssh(connection=buffer_connection.moler_connection, login="user", password="english", prompt="client:~ #",
                  host="host.domain.net", expected_prompt="host:.*#", known_hosts_on_failure='badvalue',
                  options=None)
    assert "TERM=xterm-mono ssh -l user host.domain.net" == ssh_cmd.command_string
    with pytest.raises(CommandFailure):
        ssh_cmd()


def test_ssh_failed_authentication_failed(buffer_connection, command_output_authentication_failed):
    command_output = command_output_authentication_failed
    buffer_connection.remote_inject_response([command_output])

    ssh_cmd = Ssh(connection=buffer_connection.moler_connection, login="user", password="english", prompt="client:.*$",
                  host="host.domain.net", expected_prompt="host:.*#")
    expected_cmd_str = "TERM=xterm-mono ssh -l user -o ServerAliveInterval=7 -o ServerAliveCountMax=2 host.domain.net"
    assert expected_cmd_str == ssh_cmd.command_string
    with pytest.raises(CommandFailure) as err:
        ssh_cmd()
    assert "Authentication fail" in str(err.value)


def test_ssh_timeout_with_wrong_change_prompt(buffer_connection, command_output_change_prompt):
    command_output = command_output_change_prompt
    buffer_connection.remote_inject_response([command_output])

    ssh_cmd = Ssh(connection=buffer_connection.moler_connection, login="user", password="english",
                  set_prompt=r'export PS1="\\u$"', host="host.domain.net", prompt="client.*>",
                  expected_prompt=r"wrong_user\$", prompt_after_login=r"host.*#", options=None)

    with pytest.raises(CommandTimeout):
        ssh_cmd(timeout=0.2)


def test_ssh_timeout_with_wrong_change_prompt_after_login(buffer_connection, command_output_change_prompt):
    command_output = command_output_change_prompt
    buffer_connection.remote_inject_response([command_output])

    ssh_cmd = Ssh(connection=buffer_connection.moler_connection, login="user", password="english",
                  set_prompt=r'export PS1="\\u$"', host="host.domain.net", prompt="client.*>",
                  expected_prompt=r"user\$", prompt_after_login=r"wronghost.*#", options=None)

    with pytest.raises(CommandTimeout):
        ssh_cmd(timeout=0.2)


def test_ssh_returns_proper_command_string(buffer_connection):
    ssh_cmd = Ssh(buffer_connection, login="user", password="english",
                  host="host.domain.net", expected_prompt="host:.*#", options=None)
    assert "TERM=xterm-mono ssh -l user host.domain.net" == ssh_cmd.command_string


@pytest.fixture
def command_output_authentication_failed():
    data = """TERM=xterm-mono ssh -l user -o ServerAliveInterval=7 -o ServerAliveCountMax=2 host.domain.net

You are about to access a private system. This system is for the use
of authorized users only. All connections are logged to the extent and
by means acceptable by the local legislation. Any unauthorized access
or access attempts may be punished to the fullest extent possible
under the applicable local legislation.

Password: ***************
Password: ***************
Password: ***************
user@host's password: ***************
Authentication failed.
client:~ $ """
    return data


@pytest.fixture
def command_output_failed_host_key_verification():
    data = """TERM=xterm-mono ssh -l user host.domain.net
Host key verification failed
host:~ # """
    return data


@pytest.fixture
def command_output_failed_known_hosts():
    data = """TERM=xterm-mono ssh -l user host.domain.net
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
The fingerprint for the RSA key sent by the remote host is
[...].
Please contact your system administrator.
Add correct host key in /home/you/.ssh/known_hosts to get rid of this message.
Offending RSA key in /home/you/.ssh/known_hosts:86
id_dsa:
RSA host key for host.domain.net has changed and you have requested strict checking.
Host key verification failed.
client:~ # """
    return data


@pytest.fixture
def command_output_permission_denied():
    data = """TERM=xterm-mono ssh -l user host.domain.net
Password:
Permission denied.
client:~ >"""
    return data


@pytest.fixture
def command_output_permission_denied_key():
    data = """TERM=xterm-mono ssh -l user host.domain.net
Password:
Permission denied (publickey,password,keyboard-interactive)
client:~ >"""
    return data


@pytest.fixture
def command_output_2_passwords():
    lines = [
        'TERM=xterm-mono ssh -l user host.domain.net\n',
        'You are about to access a private system. This system is for the use of\n',
        'authorized users only. All connections are logged to the extent and by means\n',
        'acceptable by the local legislation. Any unauthorized access or access attempts\n',
        'may be punished to the fullest extent possible under the applicable local',
        'legislation.\n'
        'Password:\n',
        'This account is used as a fallback account. The only thing it provides is\n'
        'the ability to switch to the root account.\n',
        '\n',
        'Please enter the root password\n',
        'Password:',
        '\n',
        'starthost:~ > '
    ]
    data = ""
    for line in lines:
        data = data + line
    return data


@pytest.fixture
def command_output_and_expected_result():
    lines = [
        'user@client:~>',
        'TERM=xterm-mono ssh -l user host.domain.net\n',
        'To edit this message please edit /etc/ssh_banner\n',
        'You may put information to /etc/ssh_banner who is owner of this PC\n',
        'Password:',
        ' \n',
        'Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1\n',
        'Have a lot of fun...\n',
        'host:~ # ',
        'export TMOUT=\"2678400\"\n',
        'host:~ # ',
    ]
    data = ""
    for line in lines:
        data = data + line
    return data


@pytest.fixture
def command_output_change_prompt():
    lines = """
client:~/>TERM=xterm-mono ssh -l user host.domain.net
Do you want to continue (yes/no)? yes
To edit this message please edit /etc/ssh_banner
You may put information to /etc/ssh_banner who is owner of this PC
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
host:~ #
host:~ # export PS1="\\u$"
user$
"""
    return lines
