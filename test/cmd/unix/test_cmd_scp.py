# -*- coding: utf-8 -*-
"""
Testing of scp command.
"""
__author__ = 'Sylwester Golonka, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'sylwester.golonka@nokia.com, marcin.usielski@nokia.com'

from moler.cmd.unix.scp import Scp
from moler.exceptions import CommandFailure
import re
import pytest


def test_scp_returns_proper_command_string(buffer_connection):
    scp_cmd = Scp(connection=buffer_connection.moler_connection, source="/home/ute/test",
                  dest="ute@localhost:/home/ute")
    assert "scp /home/ute/test ute@localhost:/home/ute" == scp_cmd.command_string


def test_scp_works_properly_on_slice_string(buffer_connection):
    slice_index = 17
    scp_cmd = Scp(connection=buffer_connection.moler_connection, source="user@127.0.0.1:/tmp/WHERE/archive_with_long_name.zip",
                  dest="/home/user/logs/VeryLongPathWithVeryDetailedInformation/Full_Auto_Pipeline_snapshots",
                  options="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r -P 22")
    scp_cmd._max_index_from_beginning = slice_index
    scp_cmd._max_index_from_end = slice_index
    command_string = r"scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r -P 22 user@127.0.0.1:/tmp/WHERE/archive_with_long_name.zip /home/user/logs/VeryLongPathWithVeryDetailedInformation/Full_Auto_Pipeline_snapshots"
    beginning_command_string = r"scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r -P 22 user@127.0.0.1:/tmp/"
    finish_command_string = r"archive_with_long_name.zip /home/user/logs/VeryLongPathWithVeryDetailedInformation/Full_Auto_Pipeline_snapshots"
    not_existing = r"No existng string in the command string"

    assert command_string == scp_cmd.command_string
    m = re.search(scp_cmd._cmd_escaped, beginning_command_string)
    assert m.group(0) == beginning_command_string[:slice_index]
    m = re.search(scp_cmd._cmd_escaped, finish_command_string)
    assert m.group(0) == finish_command_string[-slice_index:]
    m = re.search(scp_cmd._cmd_escaped, not_existing)
    assert m is None


def test_scp_works_properly_on_slice_string_beginning(buffer_connection):
    slice_index = 17
    scp_cmd = Scp(connection=buffer_connection.moler_connection, source="user@127.0.0.1:/tmp/WHERE/archive_with_long_name.zip",
                  dest="/home/user/logs/VeryLongPathWithVeryDetailedInformation/Full_Auto_Pipeline_snapshots",
                  options="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r -P 22")
    scp_cmd._max_index_from_beginning = slice_index
    scp_cmd._max_index_from_end = 0
    command_string = r"scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r -P 22 user@127.0.0.1:/tmp/WHERE/archive_with_long_name.zip /home/user/logs/VeryLongPathWithVeryDetailedInformation/Full_Auto_Pipeline_snapshots"
    beginning_command_string = r"scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r -P 22 user@127.0.0.1:/tmp/"
    finish_command_string = r"archive_with_long_name.zip /home/user/logs/VeryLongPathWithVeryDetailedInformation/Full_Auto_Pipeline_snapshots"
    not_existing = r"No existng string in the command string"

    assert command_string == scp_cmd.command_string
    m = re.search(scp_cmd._cmd_escaped, beginning_command_string)
    assert m.group(0) == beginning_command_string[:slice_index]
    m = re.search(scp_cmd._cmd_escaped, finish_command_string)
    assert m is None
    m = re.search(scp_cmd._cmd_escaped, not_existing)
    assert m is None


def test_scp_works_properly_on_slice_string_end(buffer_connection):
    slice_index = 17
    scp_cmd = Scp(connection=buffer_connection.moler_connection, source="user@127.0.0.1:/tmp/WHERE/archive_with_long_name.zip",
                  dest="/home/user/logs/VeryLongPathWithVeryDetailedInformation/Full_Auto_Pipeline_snapshots",
                  options="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r -P 22")
    scp_cmd._max_index_from_beginning = 0
    scp_cmd._max_index_from_end = slice_index
    command_string = r"scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r -P 22 user@127.0.0.1:/tmp/WHERE/archive_with_long_name.zip /home/user/logs/VeryLongPathWithVeryDetailedInformation/Full_Auto_Pipeline_snapshots"
    beginning_command_string = r"scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r -P 22 user@127.0.0.1:/tmp/"
    finish_command_string = r"archive_with_long_name.zip /home/user/logs/VeryLongPathWithVeryDetailedInformation/Full_Auto_Pipeline_snapshots"
    not_existing = r"No existng string in the command string"

    assert command_string == scp_cmd.command_string
    m = re.search(scp_cmd._cmd_escaped, beginning_command_string)
    assert m is None
    m = re.search(scp_cmd._cmd_escaped, finish_command_string)
    assert m.group(0) == finish_command_string[-slice_index:]
    m = re.search(scp_cmd._cmd_escaped, not_existing)
    assert m is None

def test_scp_raise_exception_failure(buffer_connection):
    command_output = """
    ute@debdev:~/Desktop$ scp test ute@localhost:/home/ute
    ute@localhost's password:
    test: not a regular file
    ute@debdev:~/Desktop$"""
    buffer_connection.remote_inject_response([command_output])
    scp_cmd = Scp(connection=buffer_connection.moler_connection, source="test", dest="ute@localhost:/home/ute")
    with pytest.raises(CommandFailure):
        scp_cmd()


def test_scp_raise_exception_failure_key_verification_no_key_file(buffer_connection):
    command_output = """
ute@debdev:~/Desktop$ scp test ute@localhost:/home/ute
Are you sure you want to continue connecting (yes/no)?".
Host key verification failed.
ute@debdev:~/Desktop$ scp test ute@localhost:/home/ute
ute@debdev:~/Desktop$"""
    buffer_connection.remote_inject_response([command_output])
    scp_cmd = Scp(connection=buffer_connection.moler_connection, source="test", dest="ute@localhost:/home/ute")
    with pytest.raises(CommandFailure):
        scp_cmd()


def test_scp_raise_exception_failure_key_verification_no_known_hosts_on_failure(buffer_connection):
    command_output = """
ute@debdev:~/Desktop$ scp test.txt ute@localhost:/home/ute
Are you sure you want to continue connecting (yes/no)?"
Please contact your system administrator.
Add correct host key in /home/sward/.ssh/known_hosts to get rid of this message.
Offending RSA key in /home/sward/.ssh/known_hosts:86
RSA host key for [...] has changed and you have requested strict checking.
Host key verification failed.
ute@debdev:~/Desktop$ """
    buffer_connection.remote_inject_response([command_output])
    scp_cmd = Scp(connection=buffer_connection.moler_connection, source="test.txt", dest="ute@localhost:/home/ute",
                  known_hosts_on_failure="")
    with pytest.raises(CommandFailure):
        scp_cmd()


def test_scp_raise_exception_failure_key_verification_permission_denied(buffer_connection):
    command_output = """
ute@debdev:~/Desktop$ scp test.txt ute@localhost:/home/ute
ute@localhost's password:
Permission denied, please try again.
ute@localhost's password:
Permission denied, please try again.
ute@localhost's ldap password:
Permission denied (publickey,password).
lost connection
ute@debdev:~/Desktop$"""
    buffer_connection.remote_inject_response([command_output])
    scp_cmd = Scp(connection=buffer_connection.moler_connection, source="test.txt", dest="ute@localhost:/home/ute",
                  known_hosts_on_failure="")
    with pytest.raises(CommandFailure):
        scp_cmd()


def test_scp_raise_exception_failure_not_a_directory(buffer_connection):
    command_output = """
ute@debdev:~/Desktop$ scp test ute@localhost:/home/ute
Not a directory
ute@debdev:~/Desktop$"""
    buffer_connection.remote_inject_response([command_output])
    scp_cmd = Scp(connection=buffer_connection.moler_connection, source="test", dest="ute@localhost:/home/ute",
                  known_hosts_on_failure="")
    with pytest.raises(CommandFailure):
        scp_cmd()


def test_scp_raise_exception_ldap_password(buffer_connection):
    command_output = """
ute@debdev:~/Desktop$ scp test.txt ute@localhost:/home/ute
ute@localhost's password:
ute@localhost's ldap password:
test.txt                                                            100%  104     0.1KB/s   00:00
ute@debdev:~/Desktop$"""
    buffer_connection.remote_inject_response([command_output])
    scp_cmd = Scp(connection=buffer_connection.moler_connection, source="test.txt", dest="ute@localhost:/home/ute",
                  known_hosts_on_failure="", password="pass", repeat_password=False)
    with pytest.raises(CommandFailure):
        scp_cmd()


def test_scp_raise_exception_ldap_password_coppied(buffer_connection):
    command_output = """
ute@debdev:~/Desktop$ scp test.txt ute@localhost:/home/ute
ute@localhost's password:
ute@localhost's ldap password:
test.txt                                                            100%  104     0.1KB/s   00:00
ute@debdev:~/Desktop$"""
    passwords = ("pass1", "pass2")
    buffer_connection.remote_inject_response([command_output])
    scp_cmd = Scp(connection=buffer_connection.moler_connection, source="test.txt", dest="ute@localhost:/home/ute",
                  known_hosts_on_failure="", password=passwords)
    scp_cmd()
    assert len(passwords) == 2
    assert passwords[0] == "pass1"
    assert passwords[1] == "pass2"
