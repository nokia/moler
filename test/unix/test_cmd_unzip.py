# -*- coding: utf-8 -*-
__author__ = 'Mateusz Szczurek'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'mateusz.m.szczurek@nokia.com'

import pytest
from moler.exceptions import CommandFailure

from moler.cmd.unix.unzip import Unzip


def test_unzip_returns_fail(buffer_connection):
    """
    Test if proper alarm is raised when unzip tries to extract the invalid file.

    :param buffer_connection: Simulation of a real connection with a device.
    :return: Nothing.
    """
    command_output = """
ute@debdev:~$ unzip test.zip
unzip:  cannot find or open test.zip, test.zip.zip or test.zip.ZIP.
ute@debdev:~$
"""
    buffer_connection.remote_inject_response([command_output])
    cmd = Unzip(connection=buffer_connection.moler_connection, zip_file="test.zip")
    with pytest.raises(CommandFailure):
        cmd()


def test_unzip_forbidden_to_overwrite(buffer_connection):
    """
    Test if proper alarm is raised when unzip is not allowed to overwrite the existing file.

    :param buffer_connection: Simulation of a real connection with a device.
    :return: Nothing.
    """
    command_output = """
host:~ # unzip test.zip
Archive:  test.zip
replace test.txt? [y]es, [n]o, [A]ll, [N]one, [r]ename: N
host:~ # """
    buffer_connection.remote_inject_response([command_output])
    cmd = Unzip(connection=buffer_connection.moler_connection, zip_file="test.zip")
    with pytest.raises(CommandFailure):
        cmd()


def test_unzip_filename_not_matched(buffer_connection):
    """
    Test if exception is raised when a directory cannot be created.

    :param buffer_connection: Simulation of a real connection with a device.
    :return: Nothing.
    """
    command_output = """
host:~ # unzip test.zip -d test/test
Archive:  test.zip
checkdir:  cannot create extraction directory: test/test
           No such file or directory
host:~ # """
    buffer_connection.remote_inject_response([command_output])
    cmd = Unzip(connection=buffer_connection.moler_connection, zip_file="test.zip", extract_dir="test/test")
    with pytest.raises(CommandFailure):
        cmd()
