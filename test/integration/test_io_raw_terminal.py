# -*- coding: utf-8 -*-
"""
Tests for connection shell
"""

__author__ = 'Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'marcin.usielski@nokia.com, michal.ernst@nokia.com'

import getpass

import pytest

from moler.cmd.unix.ls import Ls
from moler.cmd.unix.ping import Ping
from moler.cmd.unix.whoami import Whoami
from moler.cmd.unix.lsof import Lsof
from moler.exceptions import CommandTimeout
from moler.io.raw.terminal import ThreadedTerminal


def test_terminal_cmd_whoami_during_ping(terminal_connection):
    terminal = terminal_connection
    cmd_whoami = Whoami(connection=terminal)
    cmd_ping = Ping(connection=terminal, destination="127.0.0.1", options='-c 3')
    cmd_ping.start(timeout=3)
    cmd_whoami.start(timeout=5)
    ret_whoami = cmd_whoami.await_done(timeout=5)
    assert 'USER' in ret_whoami
    assert ret_whoami['USER'] is not None
    assert getpass.getuser() == ret_whoami['USER']
    ret_ping = cmd_ping.result()
    assert 'packets_transmitted' in ret_ping
    assert 3 == int(ret_ping['packets_transmitted'])
    assert 'packet_loss' in ret_ping
    assert 0 == int(ret_ping['packet_loss'])


def test_terminal_cmd_whoami(terminal_connection):
    terminal = terminal_connection
    terminal.debug_hex_on_non_printable_chars = True
    terminal.debug_hex_on_all_chars = True
    cmd = Whoami(connection=terminal)
    ret = cmd()
    terminal.debug_hex_on_non_printable_chars = False
    terminal.debug_hex_on_all_chars = False
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


def test_terminal_lsof(terminal_connection):
    terminal = terminal_connection
    cmd = Lsof(connection=terminal, options="| grep python | wc -l")
    ret = cmd(timeout=300)
    assert ret["NUMBER"] > 1


@pytest.yield_fixture()
def terminal_connection():
    from moler.threaded_moler_connection import ThreadedMolerConnection

    moler_conn = ThreadedMolerConnection()
    terminal = ThreadedTerminal(moler_connection=moler_conn)

    with terminal.open() as connection:
        yield connection.moler_connection
