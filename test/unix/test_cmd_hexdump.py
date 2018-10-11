# -*- coding: utf-8 -*-
"""
Hexdump command test module.
"""

__author__ = 'Agnieszka Bylica, Adrianna Pienkowska'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, adrianna.pienkowska@nokia.com'

import pytest
from moler.cmd.unix.hexdump import Hexdump
from moler.exceptions import CommandFailure


def test_hexdump_returns_proper_command_string(buffer_connection):
    hexdump_cmd = Hexdump(buffer_connection, files=["old"])
    assert "hexdump old" == hexdump_cmd.command_string


def test_hexdump_raise_error_on_wrong_option(buffer_connection, command_output_and_expected_result_on_wrong_option):
    hexdump_cmd = Hexdump(connection=buffer_connection.moler_connection, files=["old"], options='-abc')
    command_output, expected_result = command_output_and_expected_result_on_wrong_option
    buffer_connection.remote_inject_response([command_output])
    assert 'hexdump -abc old' == hexdump_cmd.command_string
    with pytest.raises(CommandFailure):
        hexdump_cmd()


def test_hexdump_raise_error_on_no_such_file(buffer_connection, command_output_and_expected_result_on_no_such_file):
    hexdump_cmd = Hexdump(connection=buffer_connection.moler_connection, files=["new5"])
    command_output, expected_result = command_output_and_expected_result_on_no_such_file
    buffer_connection.remote_inject_response([command_output])
    assert 'hexdump new5' == hexdump_cmd.command_string
    with pytest.raises(CommandFailure):
        hexdump_cmd()


@pytest.fixture
def command_output_and_expected_result_on_wrong_option():
    output = """xyz@debian:~/Dokumenty/sed$ hexdump -abc old
hexdump: invalid option -- 'a'
usage: hexdump [-bcCdovx] [-e fmt] [-f fmt_file] [-n length]
               [-s skip] [file ...]
       hd      [-bcdovx]  [-e fmt] [-f fmt_file] [-n length]
               [-s skip] [file ...]
xyz@debian:~/Dokumenty/sed$ """
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_on_no_such_file():
    output = """xyz@debian:~/Dokumenty/sed$ hexdump new5
hexdump: new5: No such file or directory
xyz@debian:~/Dokumenty/sed$ """
    result = dict()
    return output, result
