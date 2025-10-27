# -*- coding: utf-8 -*-
"""
Rm command module.
"""

__author__ = 'Bartosz Odziomek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2025, Nokia'
__email__ = 'bartosz.odziomek@nokia.com, marcin.usielski@nokia.com'


def test_rm_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.rm import Rm
    rm_cmd = Rm(connection=buffer_connection.moler_connection, file="test.txt")
    assert "rm test.txt" == rm_cmd.command_string



def test_rm_permission_denied(buffer_connection):
    from moler.cmd.unix.rm import Rm
    from moler.exceptions import MolerException
    output = """rm protected.txt
rm: cannot remove 'protected.txt': Permission denied
    cannot remove'.*': Permission denied
moler_bash#"""

    rm_cmd = Rm(connection=buffer_connection.moler_connection, file="protected.txt")
    buffer_connection.remote_inject_response([output])
    try:
        rm_cmd()
    except MolerException as exc:
        assert "Permission denied" in str(exc)
    else:
        assert False, "Exception not raised for permission denied"
