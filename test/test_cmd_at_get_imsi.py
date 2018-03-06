# -*- coding: utf-8 -*-
"""
Testing AtGetIMSI commands.
"""
import pytest

__author__ = 'Lukasz Blaszkiewicz, Kamil Kania, Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'kamil.kania@nokia.com, grzegorz.latuszek@nokia.com'


# --------------------------- testing base class ---------------------------
def test_calling_at_cmd_get_imsi_returns_expected_result(buffer_connection):
    from moler.cmd.at import get_imsi
    at_cmd_get_imsi = get_imsi.AtCmdGetIMSI(connection=buffer_connection.moler_connection)
    buffer_connection.remote_inject_response([get_imsi.COMMAND_OUTPUT])
    result = at_cmd_get_imsi()
    assert result == get_imsi.COMMAND_RESULT


def test_at_cmd_get_imsi_raises_AtCommandModeNotSupported_when_instantiated_in_read_mode():
    from moler.cmd.at.get_imsi import AtCmdGetIMSI, AtCommandModeNotSupported
    with pytest.raises(AtCommandModeNotSupported):
        AtCmdGetIMSI(operation="read")


def test_calling_at_cmd_get_imsi_in_test_mode_returns_empty_result(buffer_connection):
    from moler.cmd.at.get_imsi import AtCmdGetIMSI
    buffer_connection.remote_inject_response(["at+cimi=?\nOK\n"])
    at_cmd_get_imsi = AtCmdGetIMSI(connection=buffer_connection.moler_connection,
                                   operation="test")
    result = at_cmd_get_imsi()
    assert result == {}
