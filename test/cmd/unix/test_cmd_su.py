# -*- coding: utf-8 -*-
"""
Su command module.
"""

__author__ = 'Agnieszka Bylica, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, marcin.usielski@nokia.com'

import pytest

from moler.cmd.unix.su import Su


def test_su_returns_proper_command_string(buffer_connection):
    cmd = Su(buffer_connection, login='xyz', options='-p', password="1234", prompt=None, newline_chars=None)
    assert "su -p xyz" == cmd.command_string


def test_su_returns_proper_command_string_pwd(buffer_connection):
    cmd = Su(buffer_connection, cmd_class_name='moler.cmd.unix.pwd.Pwd')
    assert "su -c 'pwd'" == cmd.command_string


def test_su_catches_authentication_failure(buffer_connection, command_output_and_expected_result_auth):
    from moler.exceptions import CommandFailure
    command_output, expected_result = command_output_and_expected_result_auth
    buffer_connection.remote_inject_response([command_output])
    su_cmd = Su(connection=buffer_connection.moler_connection, prompt=r"xyz@debian:", expected_prompt=r"root@debian")
    with pytest.raises(CommandFailure):
        su_cmd()


def test_su_catches_command_format_failure(buffer_connection,
                                           command_output_and_expected_result_command_format_failure):
    from moler.exceptions import CommandFailure
    command_output, expected_result = command_output_and_expected_result_command_format_failure
    buffer_connection.remote_inject_response([command_output])
    su_cmd = Su(connection=buffer_connection.moler_connection)
    with pytest.raises(CommandFailure):
        su_cmd()


def test_su_catches_username_failure(buffer_connection, command_output_and_expected_result_username_failure):
    from moler.exceptions import CommandFailure
    command_output, expected_result = command_output_and_expected_result_username_failure
    buffer_connection.remote_inject_response([command_output])
    su_cmd = Su(connection=buffer_connection.moler_connection)
    with pytest.raises(CommandFailure):
        su_cmd()


def test_sudo_su(buffer_connection):
    from moler.cmd.unix.sudo import Sudo
    command_output = """sudo su -c 'pwd'
/home/auto/inv
moler_bash#"""
    expected_dict = {'full_path': '/home/auto/inv', 'path_to_current': '/home/auto', 'current_path': 'inv'}
    buffer_connection.remote_inject_response([command_output])
    cmd_su = Su(connection=buffer_connection.moler_connection, prompt=r"moler_bash#",
                cmd_class_name='moler.cmd.unix.pwd.Pwd')
    cmd_sudo = Sudo(connection=buffer_connection.moler_connection, cmd_object=cmd_su)
    ret = cmd_sudo()
    assert ret == expected_dict


def test_sudo_su_object(buffer_connection, command_output_and_expected_result_ls_l):
    from moler.cmd.unix.sudo import Sudo
    from moler.cmd.unix.ls import Ls
    command_output = command_output_and_expected_result_ls_l[0]
    expected_dict = command_output_and_expected_result_ls_l[1]
    buffer_connection.remote_inject_response([command_output])
    cmd_ls = Ls(connection=buffer_connection.moler_connection, options="-l")
    cmd_su = Su(connection=buffer_connection.moler_connection, cmd_object=cmd_ls)
    cmd_sudo = Sudo(connection=buffer_connection.moler_connection, cmd_object=cmd_su)
    ret = cmd_sudo()
    assert ret == expected_dict


def test_sudo_su_only_params(buffer_connection, command_output_and_expected_result_ls_l):
    from moler.cmd.unix.sudo import Sudo
    command_output = command_output_and_expected_result_ls_l[0]
    expected_dict = command_output_and_expected_result_ls_l[1]
    buffer_connection.remote_inject_response([command_output])
    cmd_sudo = Sudo(connection=buffer_connection.moler_connection, cmd_class_name="moler.cmd.unix.su.Su",
                    cmd_params={'cmd_class_name': 'moler.cmd.unix.ls.Ls', 'cmd_params': {'options': '-l'}})
    ret = cmd_sudo()
    assert ret == expected_dict





@pytest.fixture
def command_output_and_expected_result_auth():
    output = """xyz@debian:~/Moler$ su
Password: 
su: Authentication failure
xyz@debian:~/Moler$"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_command_format_failure():
    output = """xyz@debian:~/Moler$ su -g 
su: invalid option -- 'g'
Usage: su [options] [LOGIN]

Options:
  -c, --command COMMAND         pass COMMAND to the invoked shell
  -h, --help                    display this help message and exit
  -, -l, --login                make the shell a login shell
  -m, -p,
  --preserve-environment        do not reset environment variables, and
                                keep the same shell
  -s, --shell SHELL             use SHELL instead of the default in passwd
xyz@debian:~/Moler$"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_username_failure():
    output = """xyz@debian:~/Moler$ su kla
No passwd entry for user 'kla'
xyz@debian:~/Moler$"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_ls_l():
    output = """sudo su -c 'ls -l'
total 8
drwxr-xr-x  2 root root    4096 Sep 25  2014 bin
-rw-r--r--  1 root root      51 Dec 15 10:48 getfzmip.txt
-rw-r--r--  1 root root      24 Dec 15 10:48 getfzmip.txt-old.20171215-104858.txt
lrwxrwxrwx  1 root root      10 Mar 20  2015 logsremote -> /mnt/logs/
moler_bash#"""
    result = {

        "total": {
            "raw": "8",
            "bytes": 8,
        },

        "files": {
            "bin": {"permissions": "drwxr-xr-x", "hard_links_count": 2, "owner": "root", "group": "root",
                    "size_bytes": 4096, "size_raw": "4096", "date": "Sep 25  2014", "name": "bin", },
            "getfzmip.txt": {"permissions": "-rw-r--r--", "hard_links_count": 1, "owner": "root", "group": "root",
                             "size_bytes": 51, "size_raw": "51", "date": "Dec 15 10:48", "name": "getfzmip.txt", },
            "getfzmip.txt-old.20171215-104858.txt": {"permissions": "-rw-r--r--", "hard_links_count": 1,
                                                     "owner": "root",
                                                     "group": "root", "size_bytes": 24, "size_raw": "24",
                                                     "date": "Dec 15 10:48",
                                                     "name": "getfzmip.txt-old.20171215-104858.txt", },
            "logsremote": {"permissions": "lrwxrwxrwx", "hard_links_count": 1, "owner": "root", "group": "root",
                           "size_bytes": 10, "size_raw": "10", "date": "Mar 20  2015", "name": "logsremote",
                           "link": "/mnt/logs/"},
        },
    }
    return output, result
