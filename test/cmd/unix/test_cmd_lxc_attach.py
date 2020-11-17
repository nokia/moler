# -*- coding: utf-8 -*-
"""
LxcAttach command test module.

:copyright: Nokia Networks
:author: I_MOLER_DEV
:contact: I_MOLER_DEV@internal.nsn.com
:maintainer: I_MOLER_DEV
:contact: I_MOLER_DEV@internal.nsn.com
"""

__author__ = 'Agnieszka Bylica, Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2020, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, marcin.usielski@nokia.com'


from moler.cmd.unix.lxc_attach import LxcAttach
from moler.exceptions import CommandFailure
import pytest


def test_lxc_attach_raise_command_error(buffer_connection, command_output_and_expected_result):
    data, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response(data)
    cmd = LxcAttach(connection=buffer_connection.moler_connection, name="0x4013")
    with pytest.raises(CommandFailure):
        cmd()


@pytest.fixture()
def command_output_and_expected_result():
    data = """
lxc-attach --name=0x4013
lxc-attach: 0x4013: attach.c: lxc_attach: 843 Failed to get init pid.
root@server:~ >"""

    result = {}

    return data, result
