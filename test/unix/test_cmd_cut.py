# -*- coding: utf-8 -*-
"""
Testing of cut command.
"""

__author__ = 'Marcin Szlapa'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.szlapa@nokia.com'

from moler.cmd.unix.cut import Cut
from moler.exceptions import CommandFailure
import pytest


def test_cut_raise_exception(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    cut_cmd = Cut(connection=buffer_connection.moler_connection)
    with pytest.raises(CommandFailure):
        cut_cmd()


@pytest.fixture
def command_output_and_expected_result():
    data = """host:~ # cut
cut: you must specify a list of bytes, characters, or fields
Try 'cut --help' for more information.
host:~ #"""
    result = {
        'LINES': []
    }

<<<<<<< HEAD
    return data, result
=======
    return data, result
>>>>>>> cd17aa59d86e697839022644eb91cb6a54d6ef81
