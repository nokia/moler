# -*- coding: utf-8 -*-
"""
Testing of unzip command.

:copyright: Nokia Networks
:author: I_MOLER_DEV
:contact: I_MOLER_DEV@internal.nsn.com
:maintainer: I_MOLER_DEV
:contact: I_MOLER_DEV@internal.nsn.com
"""

import pytest
from moler.exceptions import CommandFailure

from moler.cmd.unix.unzip import Unzip

__author__ = 'Mateusz Szczurek'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'mateusz.m.szczurek@nokia.com'


def test_unzip_returns_fail(buffer_connection):
    """

    :param buffer_connection: Simulation of a real connection with a device.
    :return: Nothing
    """
    command_output = """
ute@debdev:~$ unzip test.zip
unzip:  cannot find or open test.zip, test.zip.zip or test.zip.ZIP.
ute@debdev:~$ 
"""
    buffer_connection.remote_inject_response([command_output])
    cmd = Unzip(connection=buffer_connection.moler_connection, options="unzip test.zip")
    with pytest.raises(CommandFailure):
        cmd()
