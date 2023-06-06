# -*- coding: utf-8 -*-
"""
RunScript command test module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2022, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
import re
from moler.exceptions import CommandFailure
from moler.cmd.at.run_script import RunScript


def test_run_script_cmd_returns_proper_command_string(buffer_connection):
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="AT")
    assert "AT" == cmd.command_string


def test_run_script_raise_exception(buffer_connection):
    command_output = """
    AT+CGDATA="M-RNDIS",0,0
    ERROR
    """
    buffer_connection.remote_inject_response([command_output])
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command='AT+CGDATA="M-RNDIS",0,0')
    with pytest.raises(CommandFailure):
        cmd()

def test_run_script_raise_exception_not_all_success(buffer_connection):
    command_output = """
    AT+CGDATA="M-RNDIS",0,0
    OK
    """
    buffer_connection.remote_inject_response([command_output])
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command='AT+CGDATA="M-RNDIS",0,0',
                    success_regex=["OK", re.compile("good", re.I)])
    with pytest.raises(CommandFailure):
        cmd()
