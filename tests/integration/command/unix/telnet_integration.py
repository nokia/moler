import pytest
from command.unix.telnet import Telnet


def test_calling_telnet_returns_result_parsed_from_command_output(buffer_connection):
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    telnet_cmd = Telnet(connection=buffer_connection.moler_connection, login="fzm-tdd-1", password="Nokia", port=6000,
                        host="FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net", expected_prompt="fzm-tdd-1:.*#")
    result = telnet_cmd()
    assert result == expected_result


def test_calling_telnet_timeout(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_timeout()
    buffer_connection.remote_inject_response([command_output])
    telnet_cmd = Telnet(connection=buffer_connection.moler_connection, login="fzm-tdd-1", password="Nokia", port=6000,
                        host="FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net", expected_prompt="fzm-tdd-1:.*#")
    from moler.exceptions import ConnectionObserverTimeout
    with pytest.raises(ConnectionObserverTimeout) as exception:
        telnet_cmd(timeout=1)
    assert exception is not None


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
