# -*- coding: utf-8 -*-
"""
Testing of date command.
"""
__author__ = 'Tomasz Krol'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'tomasz.krol@nokia.com'


def test_calling_date_returns_result_parsed_from_command_output(buffer_connection):
    from moler.cmd.unix.date import Date
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    date_cmd = Date(connection=buffer_connection.moler_connection)
    result = date_cmd()
    assert result == expected_result


def command_output_and_expected_result():
    data = """
tkrol@belvedere01:~> date '+DATE:%t%t%d-%m-%Y%nTIME:%t%t%H:%M:%S%nZONE:%t%t%z %Z%nEPOCH:%t%t%s%nWEEK_NUMBER:%t%-V%nDAY_OF_YEAR:%t%-j%nDAY_OF_WEEK:%t%u (%A)%nMONTH:%t%t%-m (%B)'
DATE:           14-03-2018
TIME:           14:38:18
ZONE:           +0100 CET
EPOCH:          1521034698
WEEK_NUMBER:    11
DAY_OF_YEAR:    73
DAY_OF_WEEK:    3 (Wednesday)
MONTH:          3 (March)
tkrol@belvedere01:~> 
    """

    result = {
        'DATE': {
            'FULL': '14-03-2018',
            'YEAR': '2018',
            'MONTH': '03',
            'DAY': '14'
        },
        'DAY_NAME': 'Wednesday',
        'DAY_OF_YEAR': 73,
        'DAY_OF_MONTH': 14,
        'DAY_OF_WEEK': 3,
        'EPOCH': 1521034698,
        'MONTH_NAME': 'March',
        'MONTH_NUMBER': 3,
        'TIME': {
            'FULL': '14:38:18',
            'MINUTE': '38',
            'HOUR': '14',
            'SECOND': '18',
        },
        'WEEK_NUMBER': 11,
        'ZONE': {
            'FULL': '+0100 CET',
            'SIGN': '+',
            'HOUR': '01',
            'MINUTE': '00',
            'NAME': 'CET'
        }
    }

    return data, result
