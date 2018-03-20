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
    configure_connection_logger(connection_name="fzm-tdd-1")
    buffer_connection.name = "fzm-tdd-1"  # just to have log named as we want
    buffer_connection.remote_inject_response([command_output])
    telnet_cmd = Telnet(connection=buffer_connection.moler_connection, login="fzm-tdd-1", password="Nokia", port=6000,
                        host="FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net", prompt="fzm-tdd-1:.*#")
    result = telnet_cmd()
    assert result == expected_result


def test_calling_telnet_timeout(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_timeout()
    buffer_connection.remote_inject_response([command_output])
    telnet_cmd = Telnet(connection=buffer_connection.moler_connection, login="fzm-tdd-1", password="Nokia", port=6000,
                        host="FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net", prompt="fzm-tdd-1:.*#")
    from moler.exceptions import ConnectionObserverTimeout
    with raises(ConnectionObserverTimeout) as exception:
        telnet_cmd(timeout=1)
    assert exception is not None


def test_telnet_returns_proper_command_string(buffer_connection):
    telnet_cmd = Telnet(buffer_connection, login="fzm-tdd-1", password="Nokia", port=6000,
                        host="FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net", prompt="fzm-tdd-1:.*#")
    assert "TERM=xterm-mono telnet FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net 6000" == telnet_cmd.command_string


def command_output_and_expected_result():
    lines = [
        'amu012@belvedere07:~/automation/Flexi/config>',
        ' TERM=xterm-mono telnet FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net 6000\n'
        'Login:',
        ' fzm-tdd-1\n',
        'Password:',
        ' \n',
        'Last login: Thu Nov 23 10:38:16 2017 from 10.83.200.37\n',
        'Have a lot of fun...\n',
        'fzm-tdd-1:~ # ',
        'export TMOUT=\"2678400\"\n',
        'fzm-tdd-1:~ # ',

    ]
    data = ""
    for line in lines:
        data = data + line
    result = dict()
    return data, result


def command_output_and_expected_result_timeout():
    lines = [
        'amu012@belvedere07:~/automation/Flexi/config>',
        ' TERM=xterm-mono telnet FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net 6000\n'
        'Login:',
        ' fzm-tdd-1\n',
        'Password:',
        ' \n',
        'Last login: Thu Nov 23 10:38:16 2017 from 10.83.200.37\n',
        'Have a lot of fun...\n',
        'fzm-tdd-1:~ # ',
        'export TMOUT=\"2678400\"\n',
    ]
    data = ""
    for line in lines:
        data = data + line
    result = dict()
    return data, result
