# -*- coding: utf-8 -*-
"""
Reboot command test module.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


from moler.cmd.unix.reboot import Reboot


def test_reboot_returns_proper_command_string(buffer_connection):
    reboot_cmd = Reboot(connection=buffer_connection.moler_connection)
    assert "reboot" == reboot_cmd.command_string
