# -*- coding: utf-8 -*-
"""
Testing adb_shell command.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import pytest


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


@pytest.mark.parametrize('cause', ['command not found',
                                   'No such file or directory',
                                   'error: more than one device and emulator'])
def test_calling_adb_shell_raises_CommandFailure_with_error_msg_from_cause(buffer_connection,
                                                                           cause):
    from moler.exceptions import CommandFailure
    from moler.cmd.adb import adb_shell
    buffer_connection.remote_inject_response(["adb shell\n{}\nxyz@debian ~$ ".format(cause)])
    cmd_adb_shell = adb_shell.AdbShell(connection=buffer_connection.moler_connection,
                                       expected_prompt= r'shell@adbhost:/ \$')
    with pytest.raises(CommandFailure) as error:
        cmd_adb_shell()
    assert "failed with >>Found error regex in line '{}'<<".format(cause) in str(error.value)


def test_adb_shell_displays_expected_prompt_in_str_conversion(buffer_connection):
    from moler.cmd.adb import adb_shell

    cmd_adb_shell = adb_shell.AdbShell(connection=buffer_connection.moler_connection,
                                       expected_prompt= r'shell@adbhost:/ \$')
    assert r"expected_prompt_regex:r'shell@adbhost:/ \$'" in str(cmd_adb_shell)
