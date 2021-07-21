# -*- coding: utf-8 -*-
"""
Testing of telnet command.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import pytest
import time
from moler.cmd.unix.telnet import Telnet
from moler.exceptions import CommandFailure
from dateutil import parser
import datetime


def test_calling_telnet_returns_result_parsed_from_command_output(buffer_connection, command_output_and_expected_result):
    from moler.config.loggers import configure_device_logger
    command_output, expected_result = command_output_and_expected_result
    configure_device_logger(connection_name="host")
    buffer_connection.name = "host-name"  # just to have log named as we want
    buffer_connection.remote_inject_response([command_output])
    telnet_cmd = Telnet(connection=buffer_connection.moler_connection, login="user", password="english", port=1500,
                        host="host.domain.net", expected_prompt="host:.*#")
    result = telnet_cmd()
    assert result == expected_result


def test_calling_telnet_raise_exception_command_failure(buffer_connection):
    from moler.config.loggers import configure_device_logger
    command_output ="""TERM=xterm-mono telnet host.domain.net 1500
    bash: telnet: command not found
    user@client:~>"""
    configure_device_logger(connection_name="host")
    buffer_connection.remote_inject_response([command_output])
    telnet_cmd = Telnet(connection=buffer_connection.moler_connection, login="user", password="english", port=1500,
                        host="host.domain.net", expected_prompt=r"host:.*#", prompt=r"user@client.*>")
    with pytest.raises(CommandFailure):
        telnet_cmd()


def test_telnet_username_and_login(buffer_connection):
    with pytest.raises(CommandFailure) as ex:
        Telnet(connection=buffer_connection.moler_connection, login="user", password="english", port=1500,
               host="host.domain.net", expected_prompt=r"host:.*#", prompt=r"user@client.*>",
               username="username")
    assert "not both" in str(ex)
    assert "Telnet" in str(ex)


def test_calling_telnet_raise_exception_no_more_passwords(buffer_connection):
    command_output ="""user@host01:~> TERM=xterm-mono telnet host.domain.net 1504
Login:
Login:user
Password:
Second password:
Third password:
user@host01:~> """

    buffer_connection.remote_inject_response([command_output])
    telnet_cmd = Telnet(connection=buffer_connection.moler_connection, login="user", password=["english", "polish"],
                        port=1501, host="host.domain.net", expected_prompt="host.*#", set_timeout=None,
                        repeat_password=False)
    with pytest.raises(CommandFailure):
        telnet_cmd()


def test_calling_telnet_timeout(buffer_connection, command_output_and_expected_result_timeout):
    command_output, expected_result = command_output_and_expected_result_timeout
    buffer_connection.remote_inject_response([command_output])
    telnet_cmd = Telnet(connection=buffer_connection.moler_connection, login="user", password="english", port=1500,
                        host="host.domain.net", expected_prompt="host:.*#")
    telnet_cmd.terminating_timeout = 0.1
    from moler.exceptions import CommandTimeout
    with pytest.raises(CommandTimeout):
        telnet_cmd(timeout=0.5)


def test_telnet_returns_proper_command_string(buffer_connection):
    telnet_cmd = Telnet(buffer_connection, login="user", password="english", port=1500,
                        host="host.domain.net", expected_prompt="host:.*#")
    assert "TERM=xterm-mono telnet host.domain.net 1500" == telnet_cmd.command_string


def test_telnet_with_additional_commands(buffer_connection):
    output1 = """TERM=xterm-mono telnet
    telnet> """
    output2 = """set binary
    telnet> """
    output3 = """open host.domain.net 1500
    Login:
    Login:user
    Password:
    Last login: Thu Nov 24 10:38:16 2017 from 127.0.0.1
    Have a lot of fun...
    host:~ #"""
    output4 = """^]
    telnet> """
    output5 = """mode character
    host:~ #"""
    output6 = """export TMOUT="2678400",
    host:~ #"""
    telnet_cmd = Telnet(connection=buffer_connection.moler_connection, login="user", password="english", port=1500,
                        host="host.domain.net", expected_prompt="host:.*#",
                        cmds_before_establish_connection=['set binary'],
                        cmds_after_establish_connection=['mode character'])
    assert "TERM=xterm-mono telnet" == telnet_cmd.command_string
    telnet_cmd.life_status.inactivity_timeout = 1
    telnet_cmd.start()
    time.sleep(0.1)
    buffer_connection.moler_connection.data_received(output1.encode("utf-8"), datetime.datetime.now())
    outputs = [output2, output3, output4, output5, output6]
    time.sleep(1.2)
    for output in outputs:
        buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    telnet_cmd.await_done()
    assert telnet_cmd.done() is True


def test_telnet_with_on_inactivity(buffer_connection):
    output1 = """TERM=xterm-mono telnet
    telnet> """
    output2 = """set binary
    telnet> """
    output3 = """open host.domain.net 1500
    Login:
    Login:user
    Password:
    Last login: Thu Nov 24 10:38:16 2017 from 127.0.0.1
    Have a lot of fun...
    host:~ #"""
    output4 = """^]
    telnet> """
    output5 = """mode character
    host:~ #"""
    output6 = """export TMOUT="2678400",
    host:~ #"""

    class TelnetInact(Telnet):
        def on_inactivity(self):
            self.on_inactivity_was_called = True

    telnet_cmd = TelnetInact(connection=buffer_connection.moler_connection, login="user", password="english", port=1500,
                             host="host.domain.net", expected_prompt="host:.*#",
                             cmds_before_establish_connection=['set binary'],
                             cmds_after_establish_connection=['mode character'])
    telnet_cmd.on_inactivity_was_called = False
    assert "TERM=xterm-mono telnet" == telnet_cmd.command_string
    telnet_cmd.life_status.inactivity_timeout = 1
    telnet_cmd.start()
    time.sleep(0.1)
    buffer_connection.moler_connection.data_received(output1.encode("utf-8"), datetime.datetime.now())
    outputs = [output2, output3, output4, output5, output6]
    time.sleep(1.2)
    for output in outputs:
        buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    telnet_cmd.await_done()
    assert telnet_cmd.done() is True
    assert telnet_cmd.on_inactivity_was_called is True


@pytest.fixture
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
    result['LINES'] = [
        'Login:user',
        'Password: ',
        'Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1',
        'Have a lot of fun...',
        'host:~ # export TMOUT="2678400"'
    ]
    result['LAST_LOGIN'] = {
        'KIND': 'from',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
        'WHERE': '127.0.0.1',
    }
    result['FAILED_LOGIN_ATTEMPTS'] = None
    return data, result


@pytest.fixture
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
