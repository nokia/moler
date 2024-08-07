# -*- coding: utf-8 -*-
"""
Testing of ls command.
"""
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
from moler.cmd.unix.ls import Ls
from moler.exceptions import CommandFailure


def test_lines_split(buffer_connection):
    output = r"ls *_SYSLOG*.log" +  chr(0x0D) + chr(0x0A) + "ls: cannot access '*_SYSLOG*.log': No such file or directory" + chr(0x0D) + chr(0x0A) + "moler_bash# "
    buffer_connection.remote_inject_response([output])
    ls_cmd = Ls(connection=buffer_connection.moler_connection, options="*_SYSLOG*.log")
    ls_cmd.command_string = "ls *_SYSLOG*.log"
    with pytest.raises(CommandFailure):
        ls_cmd()


def test_calling_ls_returns_result_parsed_from_command_output(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    ls_cmd = Ls(connection=buffer_connection.moler_connection)
    result = ls_cmd()
    assert result == expected_result


def test_calling_ls_returns_result_parsed_from_command_output_deb_data_recv(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    ls_cmd = Ls(connection=buffer_connection.moler_connection)
    ls_cmd.debug_data_received = True
    result = ls_cmd()
    assert result == expected_result


def test_calling_dir_getter_from_ls_command_output(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    ls_cmd = Ls(connection=buffer_connection.moler_connection, options="-l")
    ls_cmd()
    dirs = ls_cmd.get_dirs()
    expected_dirs = {
        "bin": {"permissions": "drwxr-xr-x", "hard_links_count": 2, "owner": "root", "group": "root",
                "size_bytes": 4096, "size_raw": "4096", "date": "Sep 25  2014", "name": "bin", },
        "btslog2": {"permissions": "drwxr-xr-x", "hard_links_count": 5, "owner": "root", "group": "root",
                    "size_bytes": 4096, "size_raw": "4096", "date": "Mar 20  2015", "name": "btslog2"},
    }
    assert dirs == expected_dirs


def test_calling_link_getter_from_ls_command_output(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    ls_cmd = Ls(connection=buffer_connection.moler_connection, options="-l")
    ls_cmd()
    links = ls_cmd.get_links()
    expected_links = {
        "bcn": {"permissions": "lrwxrwxrwx", "hard_links_count": 1, "owner": "root", "group": "root",
                "size_bytes": 4, "size_raw": "4", "date": "Mar 20  2015", "name": "bcn", "link": "/bcn"},
        "logsremote": {"permissions": "lrwxrwxrwx", "hard_links_count": 1, "owner": "root", "group": "root",
                       "size_bytes": 10, "size_raw": "10", "date": "Mar 20  2015", "name": "logsremote",
                       "link": "/mnt/logs/"},
    }
    assert links == expected_links


def test_calling_file_getter_from_ls_command_output(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    ls_cmd = Ls(connection=buffer_connection.moler_connection, options="-l")
    ls_cmd()
    files = ls_cmd.get_files()
    expected_files = {
        "getfzmip.txt": {"permissions": "-rw-r--r--", "hard_links_count": 1, "owner": "root", "group": "root",
                         "size_bytes": 51, "size_raw": "51", "date": "Dec 15 10:48", "name": "getfzmip.txt", },
        "getfzmip.txt-old.20171215-104858.txt": {"permissions": "-rw-r--r--", "hard_links_count": 1,
                                                 "owner": "root", "group": "root", "size_bytes": 24,
                                                 "size_raw": "24", "date": "Dec 15 10:48",
                                                 "name": "getfzmip.txt-old.20171215-104858.txt", },
    }
    assert files == expected_files


def test_ls_returns_proper_command_string(buffer_connection):
    ls_cmd = Ls(buffer_connection, options="-l")
    assert "ls -l" == ls_cmd.command_string


def test_ls_throw_ResultNotAvailableYet(buffer_connection):
    from moler.exceptions import ResultNotAvailableYet
    ls_cmd = Ls(buffer_connection, options="-l")
    with pytest.raises(ResultNotAvailableYet):
        ls_cmd.get_dirs()


@pytest.fixture
def command_output_and_expected_result():
    data = """
host:~ # ls -l
total 8
drwxr-xr-x  2 root root    4096 Sep 25  2014 bin
drwxr-xr-x  5 root root    4096 Mar 20  2015 btslog2
-rw-r--r--  1 root root      51 Dec 15 10:48 getfzmip.txt
-rw-r--r--  1 root root      24 Dec 15 10:48 getfzmip.txt-old.20171215-104858.txt
lrwxrwxrwx  1 root root       4 Mar 20  2015 bcn -> /bcn
lrwxrwxrwx  1 root root      10 Mar 20  2015 logsremote -> /mnt/logs/
host:~ #"""
    result = {
        "total": {
            "raw": "8",
            "bytes": 8
        },
        "files": {
            "bin": {"permissions": "drwxr-xr-x", "hard_links_count": 2, "owner": "root", "group": "root",
                    "size_bytes": 4096, "size_raw": "4096", "date": "Sep 25  2014", "name": "bin", },
            "btslog2": {"permissions": "drwxr-xr-x", "hard_links_count": 5, "owner": "root", "group": "root",
                        "size_bytes": 4096, "size_raw": "4096", "date": "Mar 20  2015", "name": "btslog2", },
            "getfzmip.txt": {"permissions": "-rw-r--r--", "hard_links_count": 1, "owner": "root", "group": "root",
                             "size_bytes": 51, "size_raw": "51", "date": "Dec 15 10:48", "name": "getfzmip.txt", },
            "getfzmip.txt-old.20171215-104858.txt": {"permissions": "-rw-r--r--", "hard_links_count": 1,
                                                     "owner": "root", "group": "root", "size_bytes": 24,
                                                     "size_raw": "24", "date": "Dec 15 10:48",
                                                     "name": "getfzmip.txt-old.20171215-104858.txt", },
            "bcn": {"permissions": "lrwxrwxrwx", "hard_links_count": 1, "owner": "root", "group": "root",
                    "size_bytes": 4, "size_raw": "4", "date": "Mar 20  2015", "name": "bcn", "link": "/bcn"},
            "logsremote": {"permissions": "lrwxrwxrwx", "hard_links_count": 1, "owner": "root", "group": "root",
                           "size_bytes": 10, "size_raw": "10", "date": "Mar 20  2015", "name": "logsremote",
                           "link": "/mnt/logs/"},
        },
    }
    return data, result
