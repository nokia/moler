# -*- coding: utf-8 -*-
"""
Testing of command bzip2.
"""
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
from moler.exceptions import CommandFailure
from moler.cmd.unix.bzip2 import Bzip2

def test_bzip2_returns_proper_command(buffer_connection):
    cmd_bzip = Bzip2(connection=buffer_connection.moler_connection, options=None, files='to_archive.txt')
    assert "bzip2 to_archive.txt" == cmd_bzip.command_string


def test_bzip2_no_file(buffer_connection):
    output = """bzip2 -zkfvv c
bzip2: Can't open input file c: No such file or directory.
moler_bash#"""
    cmd_bzip2 = Bzip2(connection=buffer_connection.moler_connection, options='-zkfvv', files=['c'])
    assert cmd_bzip2.command_string == "bzip2 -zkfvv c"
    buffer_connection.remote_inject_response([output])
    with pytest.raises(CommandFailure) as err:
        cmd_bzip2()
    assert "Can't open" in str(err.value)
