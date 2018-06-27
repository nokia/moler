# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import time

import pytest

from moler.device.device import Device
from moler.device.unix import Unix


def test_unix_device_can_execute_cmds():
    unix = Unix(io_type='terminal', variant='threaded')

    _wait_workaround(unix, Device.connected)

    cmd = unix.get_cmd('ls', options="-l")
    r = cmd()
    assert (r is not None)

    cmd = unix.get_cmd('whoami')
    r = cmd()
    assert (r is not None)


def test_device_unix_can_not_execute_cmds_in_incorect_state():
    unix = Unix(io_type='terminal', variant='threaded')

    _wait_workaround(unix, Unix.connected)
    unix.goto_state(Unix.not_connected)
    _wait_workaround(unix, Unix.not_connected)

    with pytest.raises(KeyError, match=r'Unknown cmds-derived class to instantiate.*'):
        unix.get_cmd(cmd_name='cd', path="/home/user/")


def _wait_workaround(unix, dest_state):
    # Workaround when goto_state is not available
    start_time = time.time()
    while unix.get_state() != dest_state:
        if time.time() - start_time > 7:  # No infinite loop
            break
        time.sleep(0.1)

    assert (unix.get_state() == dest_state)
