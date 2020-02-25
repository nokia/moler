# -*- coding: utf-8 -*-
"""
Testing adb_shell command.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


def test_calling_adb_shell_returns_expected_result(buffer_connection):
    from moler.cmd.adb import adb_shell
    cmd_adb_shell = adb_shell.AdbShell(connection=buffer_connection.moler_connection,
                                       **adb_shell.COMMAND_KWARGS_one_device)
    buffer_connection.remote_inject_response([adb_shell.COMMAND_OUTPUT_one_device])
    result = cmd_adb_shell()
    assert result == adb_shell.COMMAND_RESULT_one_device


def test_calling_adb_shell_with_serial_number_returns_expected_result(buffer_connection):
    from moler.cmd.adb import adb_shell
    cmd_adb_shell = adb_shell.AdbShell(connection=buffer_connection.moler_connection,
                                       **adb_shell.COMMAND_KWARGS_selected_device)
    buffer_connection.remote_inject_response([adb_shell.COMMAND_OUTPUT_selected_device])
    result = cmd_adb_shell()
    assert result == adb_shell.COMMAND_RESULT_selected_device
