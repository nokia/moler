# -*- coding: utf-8 -*-
"""
Mount command test module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'

import pytest
from moler.cmd.unix.mount import Mount
from moler.exceptions import CommandFailure


def test_mount_returns_proper_command_string(buffer_connection):
    mount_cmd = Mount(connection=buffer_connection.moler_connection, options='-t ext3', device='/tmp/disk.img',
                      directory='/mnt')
    assert "mount -t ext3 /tmp/disk.img /mnt" == mount_cmd.command_string


def test_mount_raise_exception(buffer_connection):
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    mount_cmd = Mount(connection=buffer_connection.moler_connection, options='-t ext3', device='/tmp/disk.img',
                      directory='/mnt')
    with pytest.raises(CommandFailure):
        mount_cmd()


@pytest.fixture
def command_output_and_expected_result():
    data = """xyz@debian:~$ mount -t ext3 /tmp/disk.img /mnt
mount: only root can use "--types" option
xyz@debian:~$"""
    result = dict()
    return data, result
