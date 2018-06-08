# -*- coding: utf-8 -*-
"""
Tests for connection shell
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.io.raw.terminal import Terminal
from moler.cmd.unix.whoami import Whoami
from moler.cmd.unix.ls import Ls
from moler.cmd.unix.env import Env
from moler.exceptions import CommandTimeout
import getpass
import pytest


def test_termial_cmd_whoami():
    terminal = terminal_connection()
    cmd = Whoami(connection=terminal)
    ret = cmd()
    terminal.close()
    assert 'USER' in ret
    assert ret['USER'] is not None
    assert getpass.getuser() == ret['USER']


def test_terminal_timeout_next_command():
    terminal = terminal_connection()
    max_nr = 5
    for i in range(1, max_nr):
        cmd = Env(connection=terminal)
        cmd.command_string = "ping 127.0.0.1"
        with pytest.raises(CommandTimeout):
            cmd(timeout=0.3)
        cmd = Whoami(connection=terminal)
        ret = cmd()
        user = ret['USER']
        assert getpass.getuser() == user
    terminal.close()


def test_terminal_whoami_ls():
    terminal = terminal_connection()
    cmd = Whoami(connection=terminal)
    ret = cmd()
    user1 = ret['USER']
    cmd = Ls(connection=terminal)
    cmd()
    cmd = Whoami(connection=terminal)
    ret = cmd()
    terminal.close()
    user2 = ret['USER']
    assert user1 == user2
    assert getpass.getuser() == user2


@pytest.fixture
def terminal_connection():
    terminal = Terminal()
    terminal.setDaemon(True)
    terminal.start()
    return terminal
