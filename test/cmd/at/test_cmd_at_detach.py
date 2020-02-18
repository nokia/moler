# -*- coding: utf-8 -*-
"""
Testing Detach command.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import pytest


def test_calling_at_cmd_detach_returns_expected_result(buffer_connection):
    from moler.cmd.at import detach
    at_cmd_detach = detach.Detach(connection=buffer_connection.moler_connection)
    at_cmd_detach.timeout = 0.5
    buffer_connection.remote_inject_response([detach.COMMAND_OUTPUT_ver_execute])
    result = at_cmd_detach()
    assert result == detach.COMMAND_RESULT_ver_execute


def test_calling_at_cmd_detach_fails_on_erroneous_output(buffer_connection):
    from moler.cmd.at import detach
    from moler.exceptions import CommandFailure

    at_cmd_detach = detach.Detach(connection=buffer_connection.moler_connection)
    at_cmd_detach.timeout = 0.5
    buffer_connection.remote_inject_response(["AT+CGATT=0\nERROR\n"])

    with pytest.raises(CommandFailure):
        at_cmd_detach()
