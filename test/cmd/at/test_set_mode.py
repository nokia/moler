# -*- coding: utf-8 -*-
"""
Testing of set_mode command.
"""
__author__ = 'Adam Klekowski'
__copyright__ = 'Copyright (C) 2021, Nokia'
__email__ = 'adam.klekowski@nokia.com'

import pytest

from moler.cmd.at.set_mode import SetMode
from moler.exceptions import WrongUsage


def test_for_incorrect_mode(buffer_connection, command_output_and_expected_result_for_line_in_use):
    with pytest.raises(WrongUsage):
        _ = SetMode(connection=buffer_connection.moler_connection, selected_mode="Incorrect")
