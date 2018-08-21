# -*- coding: utf-8 -*-
"""
Testing of scp command.
"""
__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

from moler.cmd.unix.scp import Scp
from moler.exceptions import CommandFailure
import pytest


def test_scp_returns_proper_command_string(buffer_connection):
    scp_cmd = Scp(connection=buffer_connection.moler_connection, source="/home/ute/test",
                  dest="ute@localhost:/home/ute")
    assert "scp /home/ute/test ute@localhost:/home/ute" == scp_cmd.command_string


def test_scp_raise_exception_failure(buffer_connection):
    command_output = """
    ute@debdev:~/Desktop$ scp test ute@localhost:/home/ute
    ute@localhost's password:
    test: not a regular file
    ute@debdev:~/Desktop$
    """
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
    """
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
