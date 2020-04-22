# -*- coding: utf-8 -*-
"""
Testing CommandTextualGeneric.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import pytest


def test_correct_closing_of_ctrl_c_broken_command(buffer_connection, textual_command_class):

    cmd = textual_command_class(connection=buffer_connection.moler_connection,
                                prompt=r"^adb_shell@12345678 \$")
    assert cmd.is_end_of_cmd_output(line="adb_shell@12345678 $")
    assert cmd.is_end_of_cmd_output(line="^Cadb_shell@12345678 $")
    assert not cmd.is_end_of_cmd_output(line="Xadb_shell@12345678 $")


@pytest.fixture()
def textual_command_class():
    from moler.cmd.commandtextualgeneric import CommandTextualGeneric

    class TextualCommand(CommandTextualGeneric):
        def build_command_string(self):
            return "textual_cmd"

    return TextualCommand
