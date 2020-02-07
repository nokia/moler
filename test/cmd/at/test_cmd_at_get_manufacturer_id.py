# -*- coding: utf-8 -*-
"""
Testing GetManufacturerId command.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


def test_calling_at_cmd_get_manufacturer_id_returns_expected_result(buffer_connection):
    from moler.cmd.at import get_manufacturer_id
    at_cmd_get_imsi = get_manufacturer_id.GetManufacturerId(connection=buffer_connection.moler_connection)
    buffer_connection.remote_inject_response([get_manufacturer_id.COMMAND_OUTPUT_ver_execute])
    result = at_cmd_get_imsi()
    assert result == get_manufacturer_id.COMMAND_RESULT_ver_execute
