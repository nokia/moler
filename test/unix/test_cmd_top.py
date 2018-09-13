# -*- coding: utf-8 -*-
"""
Top command test module.
"""

__author__ = 'Adrianna Pienkowska'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com'

import pytest
from moler.cmd.unix.top import Top
from moler.exceptions import CommandFailure


def test_top_returns_proper_command_string(buffer_connection):
    top_cmd = Top(buffer_connection, options='-n 3 -S -u root')
    assert "top -n 3 -S -u root n 1" == top_cmd.command_string


def test_top_raise_error_on_bad_option(buffer_connection):
    top_cmd = Top(connection=buffer_connection.moler_connection, options='abc')
    command_output, expected_result = command_output_and_expected_result_on_bad_option()
    buffer_connection.remote_inject_response([command_output])
    assert 'top abc n 1' == top_cmd.command_string
    with pytest.raises(CommandFailure):
        top_cmd()


@pytest.fixture
def command_output_and_expected_result_on_bad_option():
    output = """xyz@debian:top abc n 1
top: unknown option 'a'
Usage:
  top -hv | -bcHiOSs -d secs -n max -u|U user -p pid(s) -o field -w [cols]
xyz@debian:"""
    result = dict()
    return output, result
