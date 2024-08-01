# -*- coding: utf-8 -*-
"""
Testing of cd command 7z (class SevenZ).
"""
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
from moler.exceptions import CommandFailure
from moler.cmd.unix.seven_z import SevenZ


def test_7z_returns_proper_command_string(buffer_connection):
    cmd_7z = SevenZ(connection=buffer_connection.moler_connection, options='a', archive_file='archive.7z',
                    files='file1.txt')
    assert "7z a archive.7z file1.txt" == cmd_7z.command_string


def test_7z_returns_proper_command_string_list(buffer_connection):
    cmd_7z = SevenZ(connection=buffer_connection.moler_connection, options='a', archive_file='archive.7z',
                    files=['file1.txt', 'file2.txt', 'file3.txt'])
    assert "7z a archive.7z file1.txt file2.txt file3.txt" == cmd_7z.command_string


def test_7z_returns_proper_command_e(buffer_connection):
    cmd_7z = SevenZ(connection=buffer_connection.moler_connection, options='e', archive_file='archive.7z')
    assert "7z e archive.7z" == cmd_7z.command_string


def test_7z_no_file(buffer_connection):
    output = """7z e arch2.7z

7-Zip [64] 16.02 : Copyright (c) 1999-2016 Igor Pavlov : 2016-05-21
p7zip Version 16.02 (locale=en_US.UTF-8,Utf16=on,HugeFiles=on,64 bits,3 CPUs Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz (806EC),ASM,AES-NI)

Scanning the drive for archives:

ERROR: No more files
arch2.7z



System ERROR:
Unknown error -2147024872
moler_bash#"""
    cmd_7z = SevenZ(connection=buffer_connection.moler_connection, options='e', archive_file='arch2.7z')
    buffer_connection.remote_inject_response([output])
    with pytest.raises(CommandFailure) as err:
        cmd_7z()
    assert "No more files" in str(err.value)
