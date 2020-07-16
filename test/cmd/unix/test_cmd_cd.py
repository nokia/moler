# -*- coding: utf-8 -*-
"""
Testing of cd command.
"""
__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'michal.ernst@nokia.com'

import pytest
import datetime
from moler.util.moler_test import MolerTest
from moler.exceptions import CommandFailure


def test_calling_cd_returns_result_parsed_from_command_output(buffer_connection, command_output_and_expected_result):
    from moler.cmd.unix.cd import Cd
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    cd_cmd = Cd(connection=buffer_connection.moler_connection, path="/home/user/")
    result = cd_cmd()
    assert result == expected_result


def test_cd_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.cd import Cd
    cd_cmd = Cd(connection=buffer_connection.moler_connection, path="/home/user/")
    assert "cd /home/user/" == cd_cmd.command_string


def test_command_unicode_error(buffer_connection, command_output_and_expected_result):
    command_output, expected_result = command_output_and_expected_result
    from moler.cmd.unix.cd import Cd
    sleep_time = 0.1

    class CdUnicodeError(Cd):
        def __init__(self, *args, **kwargs):
            self.raise_unicode = True
            self.nr = 0
            super(CdUnicodeError, self).__init__(*args, **kwargs)

        def on_new_line(self, line, is_full_line):
            if self.raise_unicode:
                self.nr += 1
                exc = UnicodeDecodeError("utf-8", b'abcdef', 0, 1, "Unknown")
                raise exc
            super(CdUnicodeError, self).on_new_line(line, is_full_line)

    cmd = CdUnicodeError(connection=buffer_connection.moler_connection, path="/home/user/")
    cmd_start_string = "{}\n".format(cmd.command_string)
    cmd.start()
    MolerTest.sleep(sleep_time)
    buffer_connection.moler_connection.data_received(cmd_start_string.encode("utf-8"), datetime.datetime.now())
    MolerTest.sleep(sleep_time)
    cmd._ignore_unicode_errors = False
    cmd.raise_unicode = True
    MolerTest.sleep(sleep_time)
    buffer_connection.moler_connection.data_received("abc".encode("utf-8"), datetime.datetime.now())
    MolerTest.sleep(sleep_time)
    cmd.raise_unicode = False
    MolerTest.sleep(sleep_time)
    buffer_connection.moler_connection.data_received(command_output.encode("utf-8"), datetime.datetime.now())
    MolerTest.sleep(sleep_time)
    with pytest.raises(CommandFailure):
        cmd.await_done()

    cmd = CdUnicodeError(connection=buffer_connection.moler_connection, path="/home/user/")
    cmd.start()
    MolerTest.sleep(sleep_time)
    buffer_connection.moler_connection.data_received(cmd_start_string.encode("utf-8"), datetime.datetime.now())
    MolerTest.sleep(sleep_time)
    cmd._ignore_unicode_errors = True
    cmd.raise_unicode = True
    MolerTest.sleep(sleep_time)
    buffer_connection.moler_connection.data_received("abc".encode("utf-8"), datetime.datetime.now())
    MolerTest.sleep(sleep_time)
    cmd.raise_unicode = False
    MolerTest.sleep(sleep_time)
    buffer_connection.moler_connection.data_received(command_output.encode("utf-8"), datetime.datetime.now())
    MolerTest.sleep(sleep_time)
    cmd.await_done()


@pytest.fixture
def command_output_and_expected_result():
    data = """
host:~ # cd /home/user/
host:/home/user #  
    """
    result = {
    }
    return data, result
