# -*- coding: utf-8 -*-
"""
Tests for connection shell
"""

__author__ = 'Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com, michal.ernst@nokia.com'

import getpass

import pytest

from moler.cmd.unix.ls import Ls
from moler.cmd.unix.ping import Ping
from moler.cmd.unix.gunzip import Gunzip
from moler.cmd.unix.whoami import Whoami
from moler.exceptions import CommandTimeout
from moler.io.raw.terminal import ThreadedTerminal


def test_terminal_cmd_gunzip(terminal_connection):
    terminal = terminal_connection
    gunzip_cmd = Gunzip(connection=terminal, archive_name=['new.gz'], overwrite='True')
    assert 'gunzip new.gz' == gunzip_cmd.command_string


def test_terminal_cmd_whoami(terminal_connection):
    terminal = terminal_connection
    cmd = Whoami(connection=terminal)
    ret = cmd()
    assert 'USER' in ret
    assert ret['USER'] is not None
    assert getpass.getuser() == ret['USER']


def test_terminal_timeout_next_command(terminal_connection):
    terminal = terminal_connection
    max_nr = 5
    for i in range(1, max_nr):
        cmd = Ping(connection=terminal, destination="127.0.0.1")
        with pytest.raises(CommandTimeout):
            cmd(timeout=0.3)
        cmd = Whoami(connection=terminal)
        ret = cmd()
        user = ret['USER']
        assert getpass.getuser() == user


def test_terminal_whoami_ls(terminal_connection):
    terminal = terminal_connection
    cmd = Whoami(connection=terminal)
    ret = cmd()
    user1 = ret['USER']
    cmd = Ls(connection=terminal)
    cmd()
    cmd = Whoami(connection=terminal)
    ret = cmd()
    user2 = ret['USER']
    assert user1 == user2
    assert getpass.getuser() == user2


@pytest.yield_fixture()
def terminal_connection():
    from moler.connection import ObservableConnection

    moler_conn = ObservableConnection()
    terminal = ThreadedTerminal(moler_connection=moler_conn)

    with terminal as connection:
        yield connection.moler_connection
