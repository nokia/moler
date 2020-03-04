# -*- coding: utf-8 -*-

__author__ = 'Dariusz Rosinski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'dariusz.rosinski@nokia.com'

from moler.cmd.unix import ps


def test_ps_command_v1_short_commands(buffer_connection):
    buffer_connection.remote_inject_response([ps.COMMAND_OUTPUT])
    ps_cmd = ps.Ps(connection=buffer_connection.moler_connection, options="-o user,pid,vsz,osz,pmem,rss,cmd -e")
    assert ps_cmd.command_string == "ps -o user,pid,vsz,osz,pmem,rss,cmd -e"
    result = ps_cmd()
    assert result == ps.COMMAND_RESULT


def test_ps_command_v2_long_commands(buffer_connection):
    buffer_connection.remote_inject_response([ps.COMMAND_OUTPUT_V2])
    ps_cmd = ps.Ps(connection=buffer_connection.moler_connection, options="-ef")
    assert ps_cmd.command_string == "ps -ef"
    result = ps_cmd()
    assert result == ps.COMMAND_RESULT_V2


def test_ps_command_v3_command_field_in_the_middle(buffer_connection):
    buffer_connection.remote_inject_response([ps.COMMAND_OUTPUT_V3])
    ps_cmd = ps.Ps(connection=buffer_connection.moler_connection, options="-ef")
    assert ps_cmd.command_string == "ps -ef"
    result = ps_cmd()
    assert result == ps.COMMAND_RESULT_V3


def test_ps_command_aux(buffer_connection):
    buffer_connection.remote_inject_response([ps.COMMAND_OUTPUT_aux])
    ps_cmd = ps.Ps(connection=buffer_connection.moler_connection, options='-aux')
    assert ps_cmd.command_string == "ps -aux"
    result = ps_cmd()
    assert result == ps.COMMAND_RESULT_aux
