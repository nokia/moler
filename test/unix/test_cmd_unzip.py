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
    :return: Nothing
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
    :return: Nothing
    """
    command_output = """
ute@debdev:~$ unzip test.zip
Archive:  test.zip
replace test.txt? [y]es, [n]o, [A]ll, [N]one, [r]ename: N
ute@debdev:~$
"""
    buffer_connection.remote_inject_response([command_output])
    cmd = Unzip(connection=buffer_connection.moler_connection, zip_file="test.zip")
    with pytest.raises(CommandFailure):
        cmd()


def test_unzip_filename_not_matched(buffer_connection):
    """
    Test if proper alarm is raised when the filename is not matched.

    :param buffer_connection: Simulation of a real connection with a device.
    :return: Nothing
    """
    command_output = """
ute@debdev:~$ unzip test.zip -q /home/ute/
Archive:  test.zip
caution: filename not matched:  -q
caution: filename not matched:  /home/ute/
ute@debdev:~$
"""
    buffer_connection.remote_inject_response([command_output])
    cmd = Unzip(connection=buffer_connection.moler_connection, zip_file="test.zip", is_dir="-q", directory="/home/ute/")
    with pytest.raises(CommandFailure):
        cmd()
