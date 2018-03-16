# -*- coding: utf-8 -*-

import pytest


__author__ = 'Dariusz Rosinski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'dariusz.rosinski@nokia.com'



    #assert  RuntimeError('Wrong command passed to ps class',) == ps_cmd._exception

def test_ps_command_V1_short_commands(buffer_connection):
    from moler.cmd.unix import ps
    buffer_connection.remote_inject_response([ps.COMMAND_OUTPUT_V1])
    ps_cmd = ps.Ps(connection=buffer_connection.moler_connection)

    assert ps_cmd() == ps.COMMAND_RESULT_V1


def test_ps_command_V2_long_commands(buffer_connection):
    from moler.cmd.unix import ps
    buffer_connection.remote_inject_response([ps.COMMAND_OUTPUT_V2])
    ps_cmd = ps.Ps(connection=buffer_connection.moler_connection)

    assert ps_cmd() == ps.COMMAND_RESULT_V2

def test_ps_command_V3_command_field_in_the_middle(buffer_connection):
    from moler.cmd.unix import ps
    buffer_connection.remote_inject_response([ps.COMMAND_OUTPUT_V3])
    ps_cmd = ps.Ps(connection=buffer_connection.moler_connection)

    assert ps_cmd() == ps.COMMAND_RESULT_V3