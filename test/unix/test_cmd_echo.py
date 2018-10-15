# -*- coding: utf-8 -*-
"""
Echo command test module.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


from moler.cmd.unix.echo import Echo


def test_echo_returns_proper_command_string(buffer_connection):
    echo_cmd = Echo(connection=buffer_connection.moler_connection)
    assert "echo" == echo_cmd.command_string


def test_echo_returns_proper_command_string_with_e_option(buffer_connection):
    echo_cmd = Echo(connection=buffer_connection.moler_connection, options='-e')
    assert "echo -e" == echo_cmd.command_string


def test_echo_returns_proper_command_string_with_text(buffer_connection):
    echo_cmd = Echo(connection=buffer_connection.moler_connection, text='Hello my  beautiful   code!')
    assert "echo 'Hello my  beautiful   code!'" == echo_cmd.command_string


def test_echo_returns_proper_command_string_with_newline_chars(buffer_connection):
    echo_cmd = Echo(connection=buffer_connection.moler_connection, options='-e', text='Hello \nmy \nbeautiful \ncode!')
    assert "echo -e 'Hello \\nmy \\nbeautiful \\ncode!'" == echo_cmd.command_string


def test_echo_returns_proper_command_string_with_chars(buffer_connection):
    echo_cmd = Echo(connection=buffer_connection.moler_connection, options='-e', text='Hello \rmy \bbeautiful \tcode!')
    assert "echo -e 'Hello \\rmy \\x08beautiful \\tcode!'" == echo_cmd.command_string


def test_echo_returns_proper_command_string_with_output_file(buffer_connection):
    echo_cmd = Echo(connection=buffer_connection.moler_connection, text='Python is great!', output_file='myfile.txt')
    assert "echo 'Python is great!' > myfile.txt" == echo_cmd.command_string
