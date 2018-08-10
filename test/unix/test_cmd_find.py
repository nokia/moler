# -*- coding: utf-8 -*-
"""
Testing of find command.
"""
__author__ = 'Adrianna Pienkowska '
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com'


from moler.exceptions import CommandFailure
from moler.cmd.unix.find import Find
import pytest


def test_find_returns_proper_command_string(buffer_connection):
    find_cmd = Find(connection=buffer_connection.moler_connection, path=['sed', 'uname'], options='-H')
    assert "find -H sed uname" == find_cmd.command_string


def test_find_on_no_file_found(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_on_no_file_found()
    buffer_connection.remote_inject_response([command_output])
    find_cmd = Find(connection=buffer_connection.moler_connection, path=["Doc"], operators="-name 'my*' -type f -print")
    with pytest.raises(CommandFailure):
        find_cmd()


def test_find_on_unknown_predicate(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_on_unknown_predicate()
    buffer_connection.remote_inject_response([command_output])
    find_cmd = Find(connection=buffer_connection.moler_connection, path=["Doc"], options="-b")
    with pytest.raises(CommandFailure):
        find_cmd()


def test_find_on_operator_invalid_expression(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_on_operator_invalid_expression()
    buffer_connection.remote_inject_response([command_output])
    find_cmd = Find(connection=buffer_connection.moler_connection, path=["."], operators="-a")
    with pytest.raises(CommandFailure):
        find_cmd()


def test_find_on_bash_failure(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_on__bash_failure()
    buffer_connection.remote_inject_response([command_output])
    find_cmd = Find(connection=buffer_connection.moler_connection, path=["~"],
                    operators="( -iname 'jpeg' -o -iname 'jpg' )")
    with pytest.raises(CommandFailure):
        find_cmd()


@pytest.fixture
def command_output_and_expected_result_on_no_file_found():
    output = """xyz@debian:~$ find Doc -name 'my*' -type f -print
find: 'Doc': No such file or directory
xyz@debian:~$"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_on_unknown_predicate():
    output = """xyz@debian:~$ find -b Doc
find: unknown predicate '-b'
Try 'find --help' for more information.
xyz@debian:~$"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_on_operator_invalid_expression():
    output = """xyz@debian:~$ find . -a
find: invalid expression; you have used a binary operator '-a' with nothing before it.
xyz@debian:~$"""
    result = dict()
    return output, result


@pytest.fixture
def command_output_and_expected_result_on__bash_failure():
    output = """xyz@debian:~$ find ~ ( -iname 'jpeg' -o -iname 'jpg' )
bash: syntax error near unexpected token '('
xyz@debian:~$"""
    result = dict()
    return output, result
