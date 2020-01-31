# -*- coding: utf-8 -*-
"""
RunSerialProxy command test module.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import pytest
from moler.exceptions import CommandFailure
from moler.cmd.unix.run_serial_proxy import RunSerialProxy


def test_command_prepares_correct_commandstring_to_send(buffer_connection):
    cmd = RunSerialProxy(connection=buffer_connection.moler_connection, serial_devname="COM5")
    assert "python -i moler_serial_proxy.py COM5" == cmd.command_string


def test_calling_cmd_run_serial_proxy_returns_expected_result(buffer_connection):
    from moler.cmd.unix import run_serial_proxy
    exit = run_serial_proxy.RunSerialProxy(connection=buffer_connection.moler_connection,
                                           **run_serial_proxy.COMMAND_KWARGS)
    buffer_connection.remote_inject_response([run_serial_proxy.COMMAND_OUTPUT])
    result = exit()
    assert result == run_serial_proxy.COMMAND_RESULT


#
# def test_run_script_raise_exception(buffer_connection, command_output_and_expected_result):
#     command_output, expected_result = command_output_and_expected_result
#     buffer_connection.remote_inject_response([command_output])
#     cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh")
#     with pytest.raises(CommandFailure):
#         cmd()
#
#
# def test_run_script_not_raise_exception(buffer_connection, command_output_and_expected_result):
#     command_output, expected_result = command_output_and_expected_result
#     buffer_connection.remote_inject_response([command_output])
#     cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh", error_regex=None)
#     result = cmd()
#     assert not result
#
#
# @pytest.fixture
# def command_output_and_expected_result():
#     data = """ute@debdev:~$ ./myScript.sh
# ERROR: wrong data
# ute@debdev:~$"""
#     result = dict()
#     return data, result
