# -*- coding: utf-8 -*-
"""
Testing AtGetIMSI commands.
"""

__author__ = 'Lukasz Blaszkiewicz, Kamil Kania, Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'kamil.kania@nokia.com, grzegorz.latuszek@nokia.com'

import pytest


# --------------------------- testing base class ---------------------------
def test_calling_at_cmd_get_imsi_returns_expected_result(buffer_connection):
    from moler.cmd.at import get_imsi
    at_cmd_get_imsi = get_imsi.GetImsi(connection=buffer_connection.moler_connection,
                                       **get_imsi.COMMAND_KWARGS_ver_execute)
    buffer_connection.remote_inject_response([get_imsi.COMMAND_OUTPUT_ver_execute])
    result = at_cmd_get_imsi()
    assert result == get_imsi.COMMAND_RESULT_ver_execute


def test_at_cmd_get_imsi_raises_AtCommandModeNotSupported_when_instantiated_in_read_mode():
    from moler.cmd.at.get_imsi import GetImsi, AtCommandModeNotSupported
    with pytest.raises(AtCommandModeNotSupported):
        GetImsi(operation="read")


def test_calling_at_cmd_get_imsi_in_test_mode_returns_empty_result(buffer_connection):
    from moler.cmd.at import get_imsi
    buffer_connection.remote_inject_response([get_imsi.COMMAND_OUTPUT_ver_test])
    at_cmd_get_imsi = get_imsi.GetImsi(connection=buffer_connection.moler_connection,
                                       **get_imsi.COMMAND_KWARGS_ver_test)
    result = at_cmd_get_imsi()
    assert result == {}
