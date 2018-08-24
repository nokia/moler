# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import pytest

from moler.device.unixremote import UnixLocal
from moler.exceptions import DeviceFailure


def test_unix_device_can_execute_cmds():
    unix = UnixLocal(io_type='terminal', variant='threaded')

    cmd = unix.get_cmd('ls', options="-l")
    r = cmd()
    assert (r is not None)

    cmd = unix.get_cmd('whoami')
    r = cmd()
    assert (r is not None)


def test_device_unix_can_not_execute_cmds_in_incorect_state():
    unix = UnixLocal(io_type='terminal', variant='threaded')

    unix.goto_state(UnixLocal.not_connected)

    with pytest.raises(DeviceFailure, match=r'Failed to create .*-object for .* is unknown for state .* of device .*'):
        unix.get_cmd(cmd_name='cd', path="/home/user/")
