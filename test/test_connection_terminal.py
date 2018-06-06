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
import getpass


def test_termial_cmd_whoami():
    terminal = Terminal()
    terminal.setDaemon(True)
    terminal.start()
    cmd = Whoami(connection=terminal)
    ret = cmd()
    assert 'USER' in ret
    assert ret['USER'] is not None
    assert ret['USER'] == getpass.getuser()


def test_terminal_whoami_ls():
    terminal = Terminal()
    terminal.setDaemon(True)
    terminal.start()
    cmd = Whoami(connection=terminal)
    ret = cmd()
    user1 = ret['USER']
    cmd = Ls(connection=terminal)
    cmd()
    cmd = Whoami(connection=terminal)
    ret = cmd()
    user2 = ret['USER']
    assert user1 == user2
    assert user2 == getpass.getuser()
