# -*- coding: utf-8 -*-
"""
Testing of telnet command.
"""
from pytest import raises

from moler.cmd.unix.telnet import Telnet

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


def test_calling_telnet_returns_result_parsed_from_command_output(buffer_connection):
    from moler.config.loggers import configure_connection_logger
    command_output, expected_result = command_output_and_expected_result()
    configure_connection_logger(connection_name="host")
    buffer_connection.name = "fzm-tdd-1"  # just to have log named as we want
    buffer_connection.remote_inject_response([command_output])
    telnet_cmd = Telnet(connection=buffer_connection.moler_connection, login="user", password="Nokia", port=1500,
                        host="host.domain.net", prompt="host:.*#")
    result = telnet_cmd()
    assert result == expected_result


def test_calling_telnet_timeout(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_timeout()
    buffer_connection.remote_inject_response([command_output])
    telnet_cmd = Telnet(connection=buffer_connection.moler_connection, login="user", password="Nokia", port=1500,
                        host="host.domain.net", prompt="host:.*#")
    from moler.exceptions import CommandTimeout
    with raises(CommandTimeout) as exception:
        telnet_cmd(timeout=0.5)
    assert exception is not None


def test_telnet_returns_proper_command_string(buffer_connection):
    telnet_cmd = Telnet(buffer_connection, login="user", password="english", port=1500,
                        host="host.domain.net", prompt="host:.*#")
    assert "TERM=xterm-mono telnet host.domain.net 1500" == telnet_cmd.command_string


def command_output_and_expected_result():
    lines = [
        'user@client:~>',
        ' TERM=xterm-mono telnet host.domain.net 1500\n'
        'Login:',
        'user\n',
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
    result = dict()
    return data, result


def command_output_and_expected_result_timeout():
    lines = [
        'user@client:~>',
        ' TERM=xterm-mono telnet host.domain.net\n'
        'Login: ',
        'user\n',
        'Password:',
        ' \n',
        'Last login: Thu Nov 23 10:38:16 2017 from 10.83.200.37\n',
        'Have a lot of fun...\n',
        'host:~ # ',
        'export TMOUT=\"2678400\"\n',
    ]
    data = ""
    for line in lines:
        data = data + line
    result = dict()
    return data, result
