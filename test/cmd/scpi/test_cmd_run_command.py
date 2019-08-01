# -*- coding: utf-8 -*-
"""
RunCommand command test module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
from moler.exceptions import CommandFailure
from moler.cmd.scpi.scpi.run_command import RunCommand


def test_run_script_raise_exception(buffer_connection, command_output):
    buffer_connection.remote_inject_response([command_output])
    cmd = RunCommand(connection=buffer_connection.moler_connection, command="INP1:LEV1:ABS 1A")
    with pytest.raises(CommandFailure):
        cmd()


@pytest.fixture
def command_output():
    data = """INP1:LEV1:ABS 1A
ERROR: Wrong UNIT
SCPI>"""
    return data
