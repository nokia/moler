# -*- coding: utf-8 -*-
"""
Testing of whoami command.
"""

__author__ = 'Yeshu Yang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yeshu.yang@nokia-sbell.com'

import pytest

def test_calling_whoami_returns_result(buffer_connection, command_output_and_expected_result):
    from moler.cmd.unix.whoami import Whoami
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    whoami_cmd = Whoami(connection=buffer_connection.moler_connection)
    result = whoami_cmd()
    assert result == expected_result

# --------------------------- resources


@pytest.fixture
def command_output_and_expected_result():
    data="""
    host:~ # whoami
    ute
    host:~ #"""

    result= {
        "USER": "ute"
    }
    return data,result
