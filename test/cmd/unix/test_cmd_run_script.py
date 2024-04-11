# -*- coding: utf-8 -*-
"""
RunScript command test module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
import time
import datetime
from moler.exceptions import CommandFailure, WrongUsage, CommandTimeout
from moler.cmd.unix.run_script import RunScript


def test_run_script_cmd_returns_proper_command_string(buffer_connection):
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh")
    assert "./myScript.sh" == cmd.command_string


def test_run_script_cmd_timeout_action(buffer_connection):
    cmd1 = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh")
    cmd2 = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh")

    with pytest.raises(WrongUsage) as ex:
        cmd1.set_timeout_action('NotExisting')
    assert "Passed action: 'NotExisting' and value for all_instances: 'False'." in str(ex)
    assert cmd1.get_timeout_action() == 'c'
    assert cmd2.get_timeout_action() == 'c'

    cmd2.set_timeout_action('z')
    assert cmd1.get_timeout_action() == 'c'
    assert cmd2.get_timeout_action() == 'z'

    cmd1.set_timeout_action('z', all_instances=True)
    cmd2.set_timeout_action(None)
    assert cmd1.get_timeout_action() == 'z'
    assert cmd2.get_timeout_action() == 'z'

    with pytest.raises(WrongUsage) as ex:
        cmd2.set_timeout_action('NotExisting')
    assert "Passed action: 'NotExisting' and value for all_instances: 'False'." in str(ex)
    assert cmd1.get_timeout_action() == 'z'
    assert cmd2.get_timeout_action() == 'z'

    cmd2.set_timeout_action('c')
    assert cmd1.get_timeout_action() == 'z'
    assert cmd2.get_timeout_action() == 'c'

    cmd1.set_timeout_action(None)
    cmd2.set_timeout_action(None)
    assert cmd1.get_timeout_action() == 'z'
    assert cmd2.get_timeout_action() == 'z'

    cmd1.set_timeout_action('c', all_instances=True)
    assert cmd1.get_timeout_action() == 'c'
    assert cmd2.get_timeout_action() == 'c'


def test_run_script_ctrl_z(buffer_connection):
    output1 = "./myScript.sh"
    output1_nl = f"{output1}\n"
    output2 = "...\n"
    output3 = "[4]+  Stopped                 {output1}\n"
    output4 = "moler_bash# kill %4; wait %4\n"
    output5 = f"\n{output3}\n"
    output6 = f"[4]+  Done                 {output1}\n"
    output7 = "moler_bash#"
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command=output1)
    cmd.set_timeout_action(action='z')
    assert cmd._cmd_output_started is False
    cmd.timeout = 0.2
    assert output1 == cmd.command_string
    cmd.start(timeout=0.2)
    time.sleep(0.1)
    buffer_connection.moler_connection.data_received(output1_nl.encode("utf-8"), datetime.datetime.now())
    time.sleep(0.1)
    assert cmd._cmd_output_started is True
    buffer_connection.moler_connection.data_received(output2.encode("utf-8"), datetime.datetime.now())
    time.sleep(0.2)
    assert cmd._ctrl_z_sent is True
    assert cmd._kill_ctrl_z_sent is False
    buffer_connection.moler_connection.data_received(output3.encode("utf-8"), datetime.datetime.now())
    time.sleep(0.1)
    assert cmd._ctrl_z_sent is True
    assert cmd._kill_ctrl_z_sent is True
    buffer_connection.moler_connection.data_received(output4.encode("utf-8"), datetime.datetime.now())
    time.sleep(0.1)
    buffer_connection.moler_connection.data_received(output5.encode("utf-8"), datetime.datetime.now())
    time.sleep(0.1)
    buffer_connection.moler_connection.data_received(output6.encode("utf-8"), datetime.datetime.now())
    time.sleep(0.1)
    buffer_connection.moler_connection.data_received(output7.encode("utf-8"), datetime.datetime.now())
    assert cmd._kill_ctrl_z_job_done is True
    with pytest.raises(CommandTimeout):
        cmd.await_done()


def test_run_script_raise_exception(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh")
    with pytest.raises(CommandFailure):
        cmd()


def test_run_script_raise_exception_wrong_output(buffer_connection, command_output_lines):
    command_output, expected_result = command_output_lines
    buffer_connection.remote_inject_response([command_output])
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh",
                    success_regex="Line 3", error_regex=None)
    with pytest.raises(CommandFailure):
        cmd()


def test_run_script_proper_output(buffer_connection, command_output_lines):
    command_output, expected_result = command_output_lines
    buffer_connection.remote_inject_response([command_output])
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh",
                    success_regex=["Line 1", "Line 2"])
    result = cmd()
    assert result == expected_result


def test_run_script_not_raise_exception(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    cmd = RunScript(connection=buffer_connection.moler_connection, script_command="./myScript.sh", error_regex=None)
    result = cmd()
    assert not result


@pytest.fixture
def command_output_and_expected_result():
    data = """./myScript.sh
ERROR: wrong data
moler_bash#"""
    result = dict()
    return data, result


@pytest.fixture
def command_output_lines():
    data = """./myScript.sh
Line 1
Inter line
Line 2
moler_bash#"""
    result = dict()
    return data, result
