# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import pytest

from moler.device.unixlocal import UnixLocal
from moler.exceptions import DeviceFailure
from moler.util.moler_test import MolerTest


def test_unix_device_can_execute_cmds():
    unix = UnixLocal(io_type='terminal', variant='threaded')
    unix.establish_connection()

    cmd = unix.get_cmd(
        cmd_name='ls',
        cmd_params={
            "options": "-l"
        }
    )
    r = cmd()
    assert (r is not None)

    cmd = unix.get_cmd('whoami')
    r = cmd()
    assert (r is not None)


def test_device_unix_can_not_execute_cmds_in_incorect_state():
    unix = UnixLocal(io_type='terminal', variant='threaded')
    unix.establish_connection()

    unix.goto_state(UnixLocal.not_connected)

    with pytest.raises(DeviceFailure, match=r'Failed to create .*-object for .* is unknown for state .* of device .*'):
        unix.get_cmd(
            cmd_name='cd',
            cmd_params={
                "path": "/home/user/"
            }
        )


def test_unix_local_cmd_with_event():
    unix = UnixLocal(io_type='terminal', variant='threaded')
    unix.establish_connection()
    unix.goto_state(UnixLocal.unix_local)
    rets = {'ping': None, 'whoami': None}

    def callback_response():
        cmd_whoami = unix.get_cmd(cmd_name="whoami")
        rets['whoami'] = cmd_whoami()

    event_reconnect = unix.get_event(event_name="ping_response", event_params={})
    event_reconnect.add_event_occurred_callback(
        callback=callback_response,
    )
    event_reconnect.start()
    cmd_ping = unix.get_cmd(cmd_name="ping", cmd_params={'destination': '127.0.0.1', 'options': '-c 1'})
    rets['ping'] = cmd_ping(timeout=5)
    MolerTest.sleep(1)
    assert rets['ping'] is not None
    assert rets['whoami'] is not None
