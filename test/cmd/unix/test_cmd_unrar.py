# -*- coding: utf-8 -*-
"""
Testing of command unrar.
"""
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
from moler.exceptions import CommandFailure
from moler.cmd.unix.unrar import Unrar

def test_unrar_returns_proper_command_e(buffer_connection):
    cmd_unrar = Unrar(connection=buffer_connection.moler_connection, options='e', archive_file='archive.rar')
    assert "unrar e archive.rar" == cmd_unrar.command_string


def test_unrar_no_file(buffer_connection):
    output = """unrar e arch1.rar

UNRAR 6.21 freeware      Copyright (c) 1993-2023 Alexander Roshal

Cannot open arch1.rar
No such file or directory
No files to extract
moler_bash#"""
    cmd_unrar = Unrar(connection=buffer_connection.moler_connection, options='e', archive_file='arch1.rar')
    buffer_connection.remote_inject_response([output])
    with pytest.raises(CommandFailure) as err:
        cmd_unrar()
    assert "Cannot open" in str(err.value)
