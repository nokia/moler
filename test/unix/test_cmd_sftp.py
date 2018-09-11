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
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host="myhost.com", password='1234')
    assert "sftp myhost.com" == sftp_cmd.command_string


def test_sftp_returns_proper_command_string_options(buffer_connection):
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host="myhost.com", password='1234', options='-4')
    assert "sftp -4 myhost.com" == sftp_cmd.command_string


def test_sftp_returns_proper_command_string_user(buffer_connection):
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host="myhost.com", user="fred", password='1234')
    assert "sftp fred@myhost.com" == sftp_cmd.command_string


def test_sftp_returns_proper_command_string_pathname(buffer_connection):
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host="myhost.com", user="fred", password='1234',
                    source_path="/home/fred/homework.txt")
    assert "sftp fred@myhost.com:/home/fred/homework.txt" == sftp_cmd.command_string


def test_sftp_returns_proper_command_string_new_pathname(buffer_connection):
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host="myhost.com", user="fred", password='1234',
                    source_path="/home/fred/homework.txt", destination_path="/home/vivi/new_homework.txt")
    assert "sftp fred@myhost.com:/home/fred/homework.txt /home/vivi/new_homework.txt" == sftp_cmd.command_string


def test_sftp_returns_proper_result(buffer_connection):
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host='192.168.0.102', user='fred', password='1234',
                    options='-4', source_path='bear', destination_path='/home/xyz/Docs/bear')
    result = sftp_cmd()
    assert result == expected_result


@pytest.fixture
def command_output_and_expected_result():
    data = """xyz@debian:/home$ sftp -4 fred@192.168.0.102:bear /home/xyz/Docs/bear
The authenticity of host '192.168.0.102 (192.168.0.102)' can't be established.
ECDSA key fingerprint is SHA256:ghQ3iy/gH4YTqZOggql1eJCe3EETOOpn5yANJwFeRt0.
Are you sure you want to continue connecting (yes/no)?
Warning: Permanently added '192.168.0.102' (ECDSA) to the list of known hosts.
fred@192.168.0.102's password:
Permission denied, please try again.
fred@192.168.0.102's password:
Connected to 192.168.0.102.
Fetching /upload/bear to /home/xyz/Docs/bear
/upload/bear                                   100%   23    34.4KB/s   00:00
xyz@debian:/home$"""
    result = {'RESULT': ["Fetching /upload/bear to /home/xyz/Docs/bear",
                         "/upload/bear                                   100%   23    34.4KB/s   00:00"]}
    return data, result


def test_sftp_raises_authentication_failure(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_authentication_failure()
    buffer_connection.remote_inject_response([command_output])
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host='192.168.0.102', user='fred', password='1234',
                    source_path='cat', destination_path='/home/xyz/Docs/cat')
    with pytest.raises(CommandFailure):
        sftp_cmd()


@pytest.fixture
def command_output_and_expected_result_authentication_failure():
    data = """xyz@debian:/home$ sftp fred@192.168.0.102:cat /home/xyz/Docs/cat
fred@192.168.0.102's password:
Permission denied, please try again.
fred@192.168.0.102's password:
Permission denied, please try again.
fred@192.168.0.102's password:
Permission denied (publickey,password).
xyz@debian:/home$"""
    result = dict()
    return data, result


def test_sftp_raises_file_error_file_not_found(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_file_not_found()
    buffer_connection.remote_inject_response([command_output])
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host='192.168.0.102', user='fred', password='1234',
                    source_path='dog', destination_path='/home/xyz/Docs/dog')
    with pytest.raises(CommandFailure):
        sftp_cmd()


@pytest.fixture
def command_output_and_expected_result_file_not_found():
    data = """xyz@debian:/home$ sftp fred@192.168.0.102:dog /home/xyz/Docs/dog
fred@192.168.0.102's password:
Connected to 192.168.0.102.
File "/upload/dog" not found.
xyz@debian:/home$"""
    result = dict()
    return data, result


def test_sftp_raises_file_error_no_such_file(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_no_such_file()
    buffer_connection.remote_inject_response([command_output])
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host='192.168.0.102', user='fred', password='1234',
                    source_path='dog', destination_path='/home/xyz/Work/dog')
    with pytest.raises(CommandFailure):
        sftp_cmd()


@pytest.fixture
def command_output_and_expected_result_no_such_file():
    data = """xyz@debian:/home$ sftp fred@192.168.0.102:dog /home/xyz/Work/dog
fred@192.168.0.102's password:
Connected to 192.168.0.102.
Couldn't open local file "/home/xyz/Work/dog" for writing: No such file or directory
xyz@debian:/home$"""
    result = dict()
    return data, result


def test_sftp_raises_connection_error(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_connection_error()
    buffer_connection.remote_inject_response([command_output])
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host='192.168.0.102', user='fred', password='1234',
                    options='-6', command='get animals/pets/dog /root/dog')
    with pytest.raises(CommandFailure):
        sftp_cmd()


@pytest.fixture
def command_output_and_expected_result_connection_error():
    data = """xyz@debian:/home$ sftp -6 fred@192.168.0.102
ssh: Could not resolve hostname 192.168.0.102: Address family for hostname not supported
Couldn't read packet: Connection reset by peer
xyz@debian:/home$"""
    result = dict()
    return data, result


def test_sftp_raises_permission_denied_error(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_permission_denied()
    buffer_connection.remote_inject_response([command_output])
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host='192.168.0.102', user='fred', password='1234',
                    command='get animals/pets/dog /root/dog')
    with pytest.raises(CommandFailure):
        sftp_cmd()


@pytest.fixture
def command_output_and_expected_result_permission_denied():
    data = """xyz@debian:/home$ sftp fred@192.168.0.102
fred@192.168.0.102's password:
Connected to 192.168.0.102.
sftp>
Fetching /upload/animals/pets/dog to /root/dog
Couldn't open local file "/root/dog" for writing: Permission denied
sftp>
xyz@debian:/home$"""
    result = dict()
    return data, result


def test_sftp_raises_invalid_command_error(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_invalid_command()
    buffer_connection.remote_inject_response([command_output])
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host='192.168.0.102', user='fred', password='1234',
                    options='-i')
    with pytest.raises(CommandFailure):
        sftp_cmd()


@pytest.fixture
def command_output_and_expected_result_invalid_command():
    data = """xyz@debian:/home$ sftp -i fred@192.168.0.102
usage: sftp [-1246aCfpqrv] [-B buffer_size] [-b batchfile] [-c cipher]
          [-D sftp_server_path] [-F ssh_config] [-i identity_file] [-l limit]
          [-o ssh_option] [-P port] [-R num_requests] [-S program]
          [-s subsystem | sftp_server] host
       sftp [user@]host[:file ...]
       sftp [user@]host[:dir[/]]
       sftp -b batchfile [user@]host
xyz@debian:/home$"""
    result = dict()
    return data, result


def test_sftp_raises_invalid_option_error(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_invalid_option()
    buffer_connection.remote_inject_response([command_output])
    sftp_cmd = Sftp(connection=buffer_connection.moler_connection, host='192.168.0.102', user='fred', password='1234',
                    options='-d')
    with pytest.raises(CommandFailure):
        sftp_cmd()


@pytest.fixture
def command_output_and_expected_result_invalid_option():
    data = """xyz@debian:/home$ sftp -d fred@192.168.0.102
unknown option -- d
usage: sftp [-1246aCfpqrv] [-B buffer_size] [-b batchfile] [-c cipher]
          [-D sftp_server_path] [-F ssh_config] [-i identity_file] [-l limit]
          [-o ssh_option] [-P port] [-R num_requests] [-S program]
          [-s subsystem | sftp_server] host
       sftp [user@]host[:file ...]
       sftp [user@]host[:dir[/]]
       sftp -b batchfile [user@]host
xyz@debian:/home$"""
    result = dict()
    return data, result
