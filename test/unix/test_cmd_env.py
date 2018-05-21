# -*- coding: utf-8 -*-
"""
Testing of env command.
"""

__author__ = 'Haili Guo'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'haili.guo@nokia-sbell.com'

import pytest

def test_calling_env_returns_result(buffer_connection):
    from moler.cmd.unix.env import Env
    env_cmd = Env(connection=buffer_connection.moler_connection)
    assert "env" == env_cmd.command_string
