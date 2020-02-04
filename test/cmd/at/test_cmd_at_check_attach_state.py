# -*- coding: utf-8 -*-
"""
Testing GetAttachState command.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import pytest


# --------------------------- testing base class ---------------------------
def test_calling_at_cmd_get_attach_state_returns_expected_result(buffer_connection):
    from moler.cmd.at import get_attach_state
    at_cmd_get_attach_state = get_attach_state.GetAttachState(connection=buffer_connection.moler_connection)
    at_cmd_get_attach_state.timeout = 0.5

    buffer_connection.remote_inject_response([get_attach_state.COMMAND_OUTPUT_ver_attached])
    result = at_cmd_get_attach_state()
    assert result == get_attach_state.COMMAND_RESULT_ver_attached

    at_cmd_get_attach_state = get_attach_state.GetAttachState(connection=buffer_connection.moler_connection)
    at_cmd_get_attach_state.timeout = 0.5

    buffer_connection.remote_inject_response([get_attach_state.COMMAND_OUTPUT_ver_detached])
    result = at_cmd_get_attach_state()
    assert result == get_attach_state.COMMAND_RESULT_ver_detached


def test_calling_at_cmd_get_attach_state_fails_on_erroneous_output(buffer_connection):
    from moler.cmd.at import get_attach_state
    from moler.cmd.at.genericat import AtCommandFailure

    at_cmd_get_attach_state = get_attach_state.GetAttachState(connection=buffer_connection.moler_connection)
    at_cmd_get_attach_state.timeout = 0.5
    buffer_connection.remote_inject_response(["AT+CGATT?\nERROR\n"])

    with pytest.raises(AtCommandFailure):
        at_cmd_get_attach_state()
