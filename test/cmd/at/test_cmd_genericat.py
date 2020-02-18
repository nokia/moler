# -*- coding: utf-8 -*-
"""
Testing AT commands base class.
"""

__author__ = 'Lukasz Blaszkiewicz, Kamil Kania, Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'kamil.kania@nokia.com, grzegorz.latuszek@nokia.com'

import pytest


# --------------------------- testing base class ---------------------------


def test_at_cmd_completes_cmd_output_received_in_chunks(buffer_connection, at_cmd_test_class):
    chunks = ["AT+CIMI\n", "\n\n", "4434", "55\n", "OK\n"]
    buffer_connection.remote_inject_response(chunks)
    at_cmd = at_cmd_test_class("AT+CIMI", connection=buffer_connection.moler_connection)
    result = at_cmd(timeout=2)

    assert result["at_command_lines"] == ["443455", "OK"]


def test_at_cmd_raises_CommandTimeout_when_no_OK_received_in_cmd_output(buffer_connection, at_cmd_test_class):
    from moler.exceptions import ConnectionObserverTimeout
    at_cmd = at_cmd_test_class("AT+CIMI", connection=buffer_connection.moler_connection)
    buffer_connection.remote_inject_response(["AT+CIMI\n", "\n\n", "4434", "55\n"])
    at_cmd.start()
    with pytest.raises(ConnectionObserverTimeout):
        at_cmd.await_done(timeout=0.1)


def test_calling_at_cmd_raises_CommandFailure_when_regular_ERROR_in_at_cmd_output_occurred(buffer_connection, at_cmd_test_class):
    from moler.exceptions import CommandFailure
    buffer_connection.remote_inject_response(["AT+CMD\ndata\nERROR\n"])
    at_cmd = at_cmd_test_class("AT+CMD", connection=buffer_connection.moler_connection)
    with pytest.raises(CommandFailure) as error:
        at_cmd()
    assert 'AT+CMD' in str(error.value)
    assert "failed with >>ERROR<<" in str(error.value)


def test_calling_at_cmd_raises_CommandFailure_with_error_msg_from_at_cmd_output(buffer_connection, at_cmd_test_class):
    from moler.exceptions import CommandFailure
    buffer_connection.remote_inject_response(["AT+CMD\n+CME ERROR: no connection to phone\n"])
    at_cmd = at_cmd_test_class("AT+CMD", connection=buffer_connection.moler_connection)
    with pytest.raises(CommandFailure) as error:
        at_cmd()
    assert "failed with >>CME ERROR: no connection to phone<<" in str(error.value)
    buffer_connection.remote_inject_response(["AT+CMD\n+CMS ERROR: Short message transfer rejected\n"])
    at_cmd = at_cmd_test_class("AT+CMD", connection=buffer_connection.moler_connection)
    with pytest.raises(CommandFailure) as error:
        at_cmd()
    assert "failed with >>CMS ERROR: Short message transfer rejected<<" in str(error.value)


def test_at_cmd_raises_CommandFailure_when_instantiated_in_incorrect_mode(at_cmd_test_class):
    from moler.exceptions import CommandFailure
    with pytest.raises(CommandFailure):
        at_cmd_test_class("AT+CMD", operation="magic_mode")


# --------------------------- resources ---------------------------


@pytest.fixture
def at_cmd_test_class():
    from moler.cmd.at.genericat import GenericAtCommand

    class AtCmdTest(GenericAtCommand):
        def __init__(self, at_command_string, connection=None, operation="execute"):
            self._at_command_string = at_command_string
            super(AtCmdTest, self).__init__(connection, operation)

        def build_command_string(self):
            return self._at_command_string

        def on_new_line(self, line, is_full_line):
            if is_full_line:
                self._collect_output(line)
            return super(AtCmdTest, self).on_new_line(line, is_full_line)

        def _collect_output(self, line):
            if self._is_at_cmd_echo(line):  # skip echo
                return
            if line == "":  # skip empty lines
                return
            if "at_command_lines" not in self.current_ret:
                self.current_ret["at_command_lines"] = [line]
            else:
                self.current_ret["at_command_lines"].append(line)

    return AtCmdTest
