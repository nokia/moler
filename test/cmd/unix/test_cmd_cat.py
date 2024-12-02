# -*- coding: utf-8 -*-
"""
Testing of cat command.
"""
__author__ = 'Sylwester Golonka, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2024, Nokia'
__email__ = 'sylwester.golonka@nokia.com, marcin.usielski@nokia.com'

from moler.cmd.unix.cat import Cat
from moler.exceptions import CommandFailure, CommandTimeout
import pytest


def test_cat_returns_proper_command_string(buffer_connection):
    cat_cmd = Cat(connection=buffer_connection.moler_connection, path="/home/ute/test")
    assert "cat /home/ute/test" == cat_cmd.command_string


def test_cat_raise_exception_wrong_path(buffer_connection, command_output):
    buffer_connection.remote_inject_response([command_output])
    cat_cmd = Cat(connection=buffer_connection.moler_connection, path="/home/test/test")
    cat_cmd()


def test_cat_raise_exception_wrong_path_exception(buffer_connection, command_output_exception):
    command_output = command_output_exception
    buffer_connection.remote_inject_response([command_output])
    cat_cmd = Cat(connection=buffer_connection.moler_connection, path="/home/test/test")
    with pytest.raises(CommandFailure):
        cat_cmd()


def test_cat_raise_timeout_exception(buffer_connection, command_output_timeout_exception):
    command_output = command_output_timeout_exception
    buffer_connection.remote_inject_response([command_output])
    cat_cmd = Cat(connection=buffer_connection.moler_connection, path="/home/test/test")
    cat_cmd.terminating_timeout = 0
    with pytest.raises(CommandTimeout):
        cat_cmd(timeout=0.2)


def test_cat_raise_minimal_timeout_timeout_exception(buffer_connection, command_output_timeout_exception):
    command_output = command_output_timeout_exception
    buffer_connection.remote_inject_response([command_output])
    timeout = 0.1
    while timeout > 0:
        cat_cmd = Cat(connection=buffer_connection.moler_connection, path="/home/test/test")
        cat_cmd.terminating_timeout = 0
        cat_cmd.timeout = timeout
        try:
            cat_cmd()
        except CommandTimeout:
            pass  # we expect timeout exception
        except Exception as ex:
            msg = f"Unexpected exception {ex} for timeout={timeout}"
            raise ex
        else:
            msg = f"No exception for {timeout}, ref = {cat_cmd.result()}"
            raise Exception(msg)
        timeout /= 32.


def test_cat_prompt_in_the_same_line(buffer_connection, command_output_prompt_in_the_same_line):
    buffer_connection.remote_inject_response([command_output_prompt_in_the_same_line])
    cat_cmd = Cat(connection=buffer_connection.moler_connection, path="/home/test/test", prompt=r"^moler_bash#$")
    cat_cmd.enter_on_prompt_without_anchors = True
    cat_cmd()
    assert cat_cmd.enter_on_prompt_without_anchors is False


@pytest.fixture
def command_output():
    data = """cat /home/test/test
first line
cat: /home/ute/test: Is a directory
f6 FCT-E019-0-SmaLite \ufffd\ufffd\x7f \ufffd\ufffd\ufffd}"\ufffd\x02\ufffd?\ufffd\ufffd\ufffd\x08\ufffd\x05o\x1c
moler_bash#"""
    return data


@pytest.fixture
def command_output_exception():
    data = """cat /home/test/test
cat: /home/ute/test: Is a directory
moler_bash#"""
    return data


@pytest.fixture
def command_output_timeout_exception():
    data = """cat /home/test/test
Some data
"""
    return data


@pytest.fixture
def command_output_prompt_in_the_same_line():
    data = """
cat /home/test/test
Line 1
blamoler_bash#
moler_bash#"""
    return data
