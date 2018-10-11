# -*- coding: utf-8 -*-
"""
Userdel test module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import pytest

from moler.exceptions import CommandFailure
from moler.cmd.unix.userdel import Userdel


def test_userdel_returns_proper_command_string(buffer_connection):
    userdel_cmd = Userdel(connection=buffer_connection.moler_connection, user='xyz', prompt=None, new_line_chars=None)
    assert "userdel xyz" == userdel_cmd.command_string


def test_userdel_returns_proper_command_string_with_option(buffer_connection):
    userdel_cmd = Userdel(connection=buffer_connection.moler_connection, user='xyz', options='-R CHROOT_DIR',
                          prompt=None, new_line_chars=None)
    assert "userdel -R CHROOT_DIR xyz" == userdel_cmd.command_string


def test_userdel_raises_command_error(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    userdel_cmd = Userdel(connection=buffer_connection.moler_connection, options='-p', user='tmp_user', prompt=None,
                          new_line_chars=None)
    with pytest.raises(CommandFailure):
        userdel_cmd()


def test_userdel_raises_command_error_with_help(buffer_connection, command_output_and_expected_result_help):
    command_output, expected_result = command_output_and_expected_result_help
    buffer_connection.remote_inject_response([command_output])
    userdel_cmd = Userdel(connection=buffer_connection.moler_connection, options='-f', prompt=None, new_line_chars=None)
    with pytest.raises(CommandFailure):
        userdel_cmd()


@pytest.fixture
def command_output_and_expected_result():
    data = """xyz@debian:~$ userdel -p tmp_user
userdel: invalid option -- 'p'
xyz@debian:~$"""
    result = dict()
    return data, result


@pytest.fixture
def command_output_and_expected_result_help():
    data = """xyz@debian:~$ userdel -f
Usage: userdel [options] LOGIN

Options:
  -f, --force                   force removal of files,
                                even if not owned by user
  -h, --help                    display this help message and exit
  -r, --remove                  remove home directory and mail spool
  -R, --root CHROOT_DIR         directory to chroot into
  -Z, --selinux-user            remove any SELinux user mapping for the user


xyz@debian:~$"""
    result = dict()
    return data, result
