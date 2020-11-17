# -*- coding: utf-8 -*-
"""
LxcLs command test module.

:copyright: Nokia Networks
:author: I_MOLER_DEV
:contact: I_MOLER_DEV@internal.nsn.com
:maintainer: I_MOLER_DEV
:contact: I_MOLER_DEV@internal.nsn.com
"""

__author__ = 'Agnieszka Bylica, Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2020, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, marcin.usielski@nokia.com'


from moler.cmd.unix.lxc_ls import LxcLs
from moler.exceptions import CommandFailure
import pytest


def test_lxcls_raise_command_error(buffer_connection, command_output_and_expected_result):
    data, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response(data)
    cmd = LxcLs(connection=buffer_connection.moler_connection, options="--nesting=3")
    with pytest.raises(CommandFailure):
        cmd()


@pytest.fixture()
def command_output_and_expected_result():
    data = """lxc-ls --nesting=3
lxc-ls: attach.c: lxc_proc_get_context_info: 205 No such file or directory - Could not open /proc/26769/status.
lxc-ls: attach.c: lxc_attach: 849 Failed to get context of init process: 21769
0xe000         0xe000/0xe000
root@server:~ >"""

    result = {}

    return data, result
