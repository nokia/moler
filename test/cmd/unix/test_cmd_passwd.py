# -*- coding: utf-8 -*-
"""
Testing of passwd command.
"""
import pytest
import time

from moler.cmd.unix.passwd import Passwd
from moler.exceptions import CommandFailure

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'michal.ernst@nokia.com'


def test_passwd_raise_exception_when_passwords_do_not_match(buffer_connection,
                                                            command_output_and_expected_result_passwords_do_not_match):
    command_output, expected_result = command_output_and_expected_result_passwords_do_not_match
    buffer_connection.remote_inject_response([command_output])
    passwd_cmd = Passwd(connection=buffer_connection.moler_connection, user="user", current_password="current_password",
                        new_password="new_password")
    with pytest.raises(CommandFailure) as exc:
        passwd_cmd()

    assert "Authentication token manipulation error" in str(exc.value)


def test_passwd_raise_exception_password_too_short_and_cancel_cmd(buffer_connection,
                                                                  command_output_password_too_short_cancel_cmd):
    command_output = command_output_password_too_short_cancel_cmd.split("\n")

    passwd_cmd = Passwd(connection=buffer_connection.moler_connection, user="user", current_password="current_password",
                        new_password="new_password")
    with pytest.raises(CommandFailure) as exc:
        passwd_cmd.start()

        time.sleep(0.1)

        for line in command_output:
            if not line.endswith(": "):
                line = "{}\n".format(line)

            buffer_connection.moler_connection.data_received(line.encode("utf-8"))

        passwd_cmd.await_done(0.1)
        assert passwd_cmd.done() is True

    assert "New password is too short" in str(exc.value)


def test_passwd_raise_exception_password_too_simple_and_cancel_cmd(buffer_connection,
                                                                   command_output_password_too_simple_cancel_cmd):
    command_output = command_output_password_too_simple_cancel_cmd.split("\n")
    passwd_cmd = Passwd(connection=buffer_connection.moler_connection, user="user", current_password="current_password",
                        new_password="new_password")
    with pytest.raises(CommandFailure) as exc:
        passwd_cmd.start()

        time.sleep(0.1)

        for line in command_output:
            if not line.endswith(": "):
                line = "{}\n".format(line)

            buffer_connection.moler_connection.data_received(line.encode("utf-8"))

        passwd_cmd.await_done(0.1)
        assert passwd_cmd.done() is True

    assert "New password is too simple" in str(exc.value)


@pytest.fixture
def command_output_and_expected_result_passwords_do_not_match():
    data = """user@host:~$: passwd user
Changing password for user.
Current password:
New password:
Retype new password:
Sorry, passwords do not match.
passwd: Authentication token manipulation error
user@host:~$"""
    result = {
    }

    return data, result


@pytest.fixture
def command_output_password_too_short_cancel_cmd():
    data = """user@host:~$: passwd user
Changing password for ute.
Current password: 
New password: 
Retype new password: 
You must choose a longer password
New password: 
Retype new password: 
No password supplied
New password: 
Retype new password: 
No password supplied
passwd: Authentication token manipulation error
passwd: password unchanged
user@host:~$"""

    return data


@pytest.fixture
def command_output_password_too_simple_cancel_cmd():
    data = """user@host:~$: passwd user
Changing password for ute.
Current password: 
New password: 
Retype new password: 
Bad: new password is too simple
New password: 
Retype new password: 
No password supplied
New password: 
Retype new password: 
No password supplied
passwd: Authentication token manipulation error
passwd: password unchanged
user@host:~$"""

    return data
