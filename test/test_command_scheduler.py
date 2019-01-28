# -*- coding: utf-8 -*-
"""
Tests for CommandScheduler
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from moler.cmd.unix.ls import Ls
from moler.cmd.unix.whoami import Whoami
from moler.command_scheduler import CommandScheduler
import time


def test_add_when_empty(buffer_connection):
    cmd = Ls(connection=buffer_connection)
    assert CommandScheduler.add_command_to_connection(cmd) is True
    CommandScheduler.remove_command_from_connection(cmd)


def test_add_when_queue_occupied(buffer_connection):
    cmd1 = Ls(connection=buffer_connection)
    cmd2 = Whoami(connection=buffer_connection)
    assert CommandScheduler.add_command_to_connection(cmd1) is True
    assert CommandScheduler.add_command_to_connection(cmd2, wait_for_slot=False) is False
    CommandScheduler.remove_command_from_connection(cmd1)
    assert CommandScheduler.add_command_to_connection(cmd2, wait_for_slot=False) is True
    CommandScheduler.remove_command_from_connection(cmd2)


def test_add_when_queue_occupied_wait(buffer_connection):
    cmd1 = Ls(connection=buffer_connection)
    cmd2 = Whoami(connection=buffer_connection)
    for cmd in [cmd1, cmd2]:
        cmd.timeout = 0.1
        cmd.start_time = time.time()
    assert CommandScheduler.add_command_to_connection(cmd1) is True
    assert CommandScheduler.add_command_to_connection(cmd2, wait_for_slot=True) is False
    CommandScheduler.remove_command_from_connection(cmd1)
    assert CommandScheduler.add_command_to_connection(cmd2, wait_for_slot=True) is True
    CommandScheduler.remove_command_from_connection(cmd2)
