# -*- coding: utf-8 -*-
"""
Testing GetImei command.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


def test_calling_at_cmd_get_imei_returns_expected_result(buffer_connection):
    from moler.cmd.at import get_imei
    at_cmd_get_imsi = get_imei.GetImei(connection=buffer_connection.moler_connection)
    buffer_connection.remote_inject_response([get_imei.COMMAND_OUTPUT_ver_default])
    result = at_cmd_get_imsi()
    assert result == get_imei.COMMAND_RESULT_ver_default


def test_calling_at_cmd_get_imei_ver_imei_returns_expected_result(buffer_connection):
    from moler.cmd.at import get_imei
    at_cmd_get_imsi = get_imei.GetImei(connection=buffer_connection.moler_connection,
                                       **get_imei.COMMAND_KWARGS_ver_imei)
    buffer_connection.remote_inject_response([get_imei.COMMAND_OUTPUT_ver_imei])
    result = at_cmd_get_imsi()
    assert result == get_imei.COMMAND_RESULT_ver_imei
