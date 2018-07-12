# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import time

import pytest

from moler.device.unixremote import UnixRemote
from moler.exceptions import DeviceFailure
from moler.device.textualdevice import TextualDevice


def test_unix_device_can_execute_cmds():
    unix = UnixRemote(io_type='terminal', variant='threaded')

    cmd = unix.get_cmd('ls', options="-l")
    r = cmd()
    assert (r is not None)

    cmd = unix.get_cmd('whoami')
    r = cmd()
    assert (r is not None)


def test_device_unix_can_not_execute_cmds_in_incorect_state():
    unix = UnixRemote(io_type='terminal', variant='threaded')

    unix.goto_state(UnixRemote.not_connected)

    with pytest.raises(DeviceFailure, match=r'Failed to create .*-object for .* is unknown for state .* of device .*'):
        unix.get_cmd(cmd_name='cd', path="/home/user/")

#
# def _wait_workaround(unix, dest_state):
#     # Workaround when goto_state is not available
#     start_time = time.time()
#     while unix.current_state != dest_state:
#         if time.time() - start_time > 7:  # No infinite loop
#             break
#         time.sleep(0.1)
#
#     assert (unix.current_state == dest_state)
#
# def test_device_unix_connect_to_remote_host(get_configuration):
#     unix = UnixRemote(io_type='terminal', variant='threaded')
#     unix.configure_state_machine(get_configuration)
#     # _wait_workaround(unix, Unix.connected)
#     unix.goto_state(UnixRemote.remote)
#     # _wait_workaround(unix, Unix.unix)
#     # unix.io_connection.moler_connection.sendline("exit")
#     # _wait_workaround(unix, Unix.connected)
#     unix.goto_state(UnixRemote.not_connected)
#     _wait_workaround(unix, UnixRemote.not_connected)
#     print(unix.current_state)
#
# def test_device_unix_sm_change_state_on_send_exit(get_configuration):
#     unix = UnixRemote(io_type='terminal', variant='threaded')
#     unix.configure_state_machine(get_configuration)
#     # _wait_workaround(unix, Unix.connected)
#     unix.goto_state(UnixRemote.remote)
#     # _wait_workaround(unix, Unix.unix)
#     unix.io_connection.moler_connection.sendline("exit")
#     _wait_workaround(unix, UnixRemote.connected)
#     print(unix.current_state)
#
# @pytest.fixture(scope="module", autouse=True)
# def configure_logging():
#     import logging
#     logging.basicConfig(level=logging.DEBUG)
#     logging.getLogger('moler').setLevel(logging.DEBUG)
#     logging.getLogger('moler').propagate=True
#
# @pytest.fixture()
# def get_configuration():
#     configuration = {
#         TextualDevice.connected: {
#             UnixRemote.remote: {
#                 "execute_command": "ssh",
#                 "host": "localhost",
#                 "login": "root",
#                 "password": "emssim",
#                 "prompt": "ute@debdev:~>",
#                 "expected_prompt": 'root@debdev:~#'
#             }
#         },
#         UnixRemote.remote: {
#             TextualDevice.connected: {
#                 "execute_command": "exit",
#                 "prompt": r'^bash-\d+\.*\d*'
#             }
#         }
#     }
#
#     return configuration
