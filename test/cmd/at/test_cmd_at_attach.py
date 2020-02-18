# -*- coding: utf-8 -*-
"""
Testing Attach command.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import pytest


def test_at_cmd_attach_has_default_timeout_180sec(buffer_connection):
    from moler.cmd.at import attach
    at_cmd_attach = attach.Attach(connection=buffer_connection.moler_connection,
                                  **attach.COMMAND_KWARGS_ver_execute)
    assert at_cmd_attach.timeout == 180


def test_calling_at_cmd_attach_timeouts_after_500ms(buffer_connection):
    from moler.cmd.at import attach
    from moler.exceptions import CommandTimeout
    import time
    at_cmd_attach = attach.Attach(connection=buffer_connection.moler_connection,
                                  **attach.COMMAND_KWARGS_ver_execute)
    at_cmd_attach.timeout = 0.5
    buffer_connection.remote_inject_response(["AT+CGATT=1\n"])
    start_time = time.time()
    with pytest.raises(CommandTimeout):
        at_cmd_attach()
    duration = time.time() - start_time
    assert duration > 0.5
    assert duration < 0.7


def test_calling_at_cmd_attach_timeouts_on_no_output(buffer_connection):
    from moler.cmd.at import attach
    from moler.exceptions import CommandTimeout
    import time
    at_cmd_attach = attach.Attach(connection=buffer_connection.moler_connection,
                                  **attach.COMMAND_KWARGS_ver_execute)
    at_cmd_attach.timeout = 0.5
    start_time = time.time()
    with pytest.raises(CommandTimeout):
        at_cmd_attach()
    duration = time.time() - start_time
    assert duration > 0.5
    assert duration < 0.7


def test_calling_at_cmd_attach_returns_expected_result(buffer_connection):
    from moler.cmd.at import attach
    at_cmd_attach = attach.Attach(connection=buffer_connection.moler_connection,
                                  **attach.COMMAND_KWARGS_ver_execute)
    at_cmd_attach.timeout = 0.5
    buffer_connection.remote_inject_response([attach.COMMAND_OUTPUT_ver_execute])
    result = at_cmd_attach()
    assert result == attach.COMMAND_RESULT_ver_execute


def test_calling_at_cmd_attach_fails_on_erroneous_output(buffer_connection):
    from moler.cmd.at import attach
    from moler.exceptions import CommandFailure

    at_cmd_attach = attach.Attach(connection=buffer_connection.moler_connection,
                                  **attach.COMMAND_KWARGS_ver_execute)
    at_cmd_attach.timeout = 0.5
    buffer_connection.remote_inject_response(["AT+CGATT=1\nERROR\n"])

    with pytest.raises(CommandFailure):
        at_cmd_attach()
