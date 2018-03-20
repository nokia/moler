# -*- coding: utf-8 -*-
"""
Testing of ssh command.
"""
from moler.cmd.unix.ssh import Ssh

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


def test_calling_ssh_returns_result_parsed_from_command_output(buffer_connection):
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])

    ssh_cmd = Ssh(connection=buffer_connection.moler_connection, login="fzm-tdd-1", password="Nokia",
                  host="FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net", prompt="fzm-tdd-1:.*#")
    result = ssh_cmd()
    assert result == expected_result


def test_ssh_returns_proper_command_string(buffer_connection):
    ssh_cmd = Ssh(buffer_connection, login="fzm-tdd-1", password="Nokia",
                  host="FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net", prompt="fzm-tdd-1:.*#")
    assert "TERM=xterm-mono ssh -l fzm-tdd-1 FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net" == ssh_cmd.command_string


def command_output_and_expected_result():
    lines = [
        'amu012@belvedere07:~/automation/Flexi/config>',
        'TERM=xterm-mono ssh -l fzm-tdd-1 FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net\n',
        'To edit this message please edit /etc/ssh_banner\n',
        'You may put information to /etc/ssh_banner who is owner of this PC\n',
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
