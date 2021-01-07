# -*- coding: utf-8 -*-
"""
Testing of cu command.
"""
__author__ = 'Adam Klekowski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'adam.klekowski@nokia.com'

import pytest

from moler.cmd.at.cu import Cu
from moler.exceptions import CommandFailure


def test_find_on_no_file_found(buffer_connection, command_output_and_expected_result_for_line_in_use):
    command_output, expected_result = command_output_and_expected_result_for_line_in_use
    buffer_connection.remote_inject_response([command_output])
    cu_cmd = Cu(connection=buffer_connection.moler_connection, serial_devname="5")
    with pytest.raises(CommandFailure):
        cu_cmd()


@pytest.fixture
def command_output_and_expected_result_for_line_in_use():
    output = """user-lab0@PLKR-SC5G-PC16:~$ cu -l /dev/ttyS5 -s 19200 -E '-'
cu: open (/dev/ttyS5): Input/output error
cu: /dev/ttyS5: Line in use
user-lab0@PLKR-SC5G-PC16:~$"""
    result = dict()
    return output, result
