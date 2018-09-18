# -*- coding: utf-8 -*-
"""
Last modification: adding support for testing EPC tables and partially empty tables changes till 23.05.2018
Test for reading by columns
"""

__author__ = 'Rosinski Dariusz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'dariusz.rosinski@nokia.com'

def test_tabletext_command_command_field_in_the_middle():
    from moler.parser import table_text
    t_text = table_text.TableText(table_text.COMMAND_KWARGS["_header_regexps"],
                                  table_text.COMMAND_KWARGS["_header_keys"],
                                  _skip='drosinsk',
                                  _finish='finisher')

    lines = table_text.COMMAND_OUTPUT.split('\n')
    result = list()
    for i in lines:
        z = t_text.parse(i)
        if z is not None:
            result.append(z)

    assert result == table_text.COMMAND_RESULT


def test_tabletext_command_command_field_in_the_middle_different_split():
    from moler.parser import table_text
    t_text = table_text.TableText(table_text.COMMAND_KWARGS_V2["_header_regexps"],
                                  table_text.COMMAND_KWARGS_V2["_header_keys"],
                                  _skip='drosinsk',
                                  _finish='finisher',
                                  value_splitter=r'[\s\|]+')

    lines = table_text.COMMAND_OUTPUT_V2.split('\n')
    result = list()
    for i in lines:
        z = t_text.parse(i)
        if z is not None:
            result.append(z)

    assert result == table_text.COMMAND_RESULT_V2


def test_tabletext_output_from_epcsim():
    from moler.parser import table_text
    t_text = table_text.TableText(table_text.COMMAND_KWARGS_V3["_header_regexps"],
                                  table_text.COMMAND_KWARGS_V3["_header_keys"],
                                  table_text.COMMAND_KWARGS_V3["_skip"],
                                  _finish='finisher',
                                  value_splitter=r'[\s\|]+')

    lines = table_text.COMMAND_OUTPUT_V3.split('\n')
    result = list()
    for i in lines:
        z = t_text.parse(i)
        if z is not None:
            result.append(z)

    assert result == table_text.COMMAND_RESULT_V3


def test_tabletext_for_emty_value_field():
    from moler.parser import table_text
    t_text = table_text.TableText(table_text.COMMAND_KWARGS_V4["_header_regexps"],
                                  table_text.COMMAND_KWARGS_V4["_header_keys"],
                                  _skip='drosinsk',
                                  _finish='finisher',
                                  value_splitter=r'\s+')

    lines = table_text.COMMAND_OUTPUT_V4.split('\n')
    result = list()
    for i in lines:
        z = t_text.parse(i)
        if z is not None:
            result.append(z)

    assert result == table_text.COMMAND_RESULT_V4
