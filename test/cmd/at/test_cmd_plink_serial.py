# -*- coding: utf-8 -*-
"""
RunSerialProxy command test module.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import pytest
import time
from moler.exceptions import CommandFailure
from moler.cmd.at import plink_serial


def test_command_prepares_correct_commandstring_to_send(buffer_connection):
    cmd = plink_serial.PlinkSerial(connection=buffer_connection.moler_connection, serial_devname="COM5")
    expected_cmd_string = 'plink -serial COM5 |& awk -v entry_prompt="COM5> port READY"' + \
                          ' -v ctrlc="^C" -v exit_prompt="${PS1@P}"' + \
                          " 'BEGIN {print entry_prompt} {print} END {print ctrlc; print exit_prompt}'"
    assert expected_cmd_string == cmd.command_string


def test_calling_cmd_run_serial_proxy_returns_expected_result(buffer_connection):
    run = plink_serial.PlinkSerial(connection=buffer_connection.moler_connection,
                                   **plink_serial.COMMAND_KWARGS)
    buffer_connection.remote_inject_response([plink_serial.COMMAND_OUTPUT])
    result = run()
    assert result == plink_serial.COMMAND_RESULT


def test_command_quickly_fails_on_error(buffer_connection, command_output_from_failed_command):
    run = plink_serial.PlinkSerial(connection=buffer_connection.moler_connection,
                                   prompt="user@host", serial_devname="COM5")
    buffer_connection.remote_inject_response([command_output_from_failed_command])
    start_time = time.time()
    with pytest.raises(CommandFailure):
        run()
    assert (time.time() - start_time) < 0.8


no_plink = """
plink -serial COM5 |& awk -v entry_prompt="COM5> port READY" -v ctrlc="^C" -v exit_prompt="${PS1@P}" 'BEGIN {print entry_prompt} {print} END {print ctrlc; print exit_prompt}'
-bash: plink: command not found
^C
user@host ~
$ 

user@host ~"""

no_awk = """
plink -serial COM5 |& awk -v entry_prompt="COM5> port READY" -v ctrlc="^C" -v exit_prompt="${PS1@P}" 'BEGIN {print entry_prompt} {print} END {print ctrlc; print exit_prompt}'
-bash: awk: command not found

user@host ~"""


@pytest.fixture(params=['no plink on remote', 'no awk on remote'])
def command_output_from_failed_command(request):
    if request.param == 'no plink on remote':
        return no_plink
    else:
        return no_awk
