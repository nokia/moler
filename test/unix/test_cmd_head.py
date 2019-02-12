# -*- coding: utf-8 -*-
"""
Testing of head command.
"""
__author__ = 'Mateusz Szczurek, Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'mateusz.m.szczurek@nokia.com, sylwester.golonka@nokia.com'

from moler.cmd.unix.head import Head
from moler.exceptions import CommandFailure
import pytest


def test_head_raise_exception(buffer_connection):
    """
    Test if proper alarm is raised when head tries to open non existing file.

    :param buffer_connection: Simulation of a real connection with a device.
    :return: Nothing
    """
    command_output = """
host:~ # head test.txt
head: cannot open "test.txt" for reading: No such file or directory
host:~ #
"""
    buffer_connection.remote_inject_response([command_output])
    cmd = Head(connection=buffer_connection.moler_connection, path="test.txt")
    with pytest.raises(CommandFailure):
        cmd()
