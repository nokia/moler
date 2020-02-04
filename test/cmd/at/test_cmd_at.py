# -*- coding: utf-8 -*-
"""
Testing AT commands.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


def test_calling_at_cmd_at_returns_expected_result(buffer_connection):
    from moler.cmd.at import at
    at_cmd_at = at.At(connection=buffer_connection.moler_connection,
                      **at.COMMAND_KWARGS_ver_execute)
    buffer_connection.remote_inject_response([at.COMMAND_OUTPUT_ver_execute])
    result = at_cmd_at()
    assert result == at.COMMAND_RESULT_ver_execute
