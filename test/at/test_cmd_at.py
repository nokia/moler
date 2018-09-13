# -*- coding: utf-8 -*-
"""
Testing AT commands.
"""

__author__ = 'Lukasz Blaszkiewicz, Kamil Kania, Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'kamil.kania@nokia.com, grzegorz.latuszek@nokia.com'

import pytest


# --------------------------- testing base class ---------------------------


def test_at_cmd_completes_cmd_output_received_in_chunks(buffer_connection, at_cmd_test_class):
    chunks = ["at+cimi\n", "\n\n", "4434", "55\n", "OK\n"]
    buffer_connection.remote_inject_response(chunks)
    at_cmd = at_cmd_test_class(connection=buffer_connection.moler_connection)
    at_cmd(timeout=0.1)

    assert at_cmd.command_output == "".join(chunks)


def test_at_cmd_raises_CommandTimeout_when_no_OK_received_in_cmd_output(buffer_connection, at_cmd_test_class):
    from moler.exceptions import ConnectionObserverTimeout
    at_cmd = at_cmd_test_class(connection=buffer_connection.moler_connection)
    buffer_connection.remote_inject_response(["at+cimi\n", "\n\n", "4434", "55\n"])
    at_cmd.start()
    with pytest.raises(ConnectionObserverTimeout):
        at_cmd.await_done(timeout=0.1)


@pytest.mark.parametrize("cmd_mode, expected_cmd_string",
                         [("read", "AT+CMD?"),
                          ("test", "AT+CMD=?")])
def test_at_cmd_string_extended_with_operation_sign_when_instantiated_in_no_default_mode(cmd_mode, expected_cmd_string, at_cmd_test_class):
    assert at_cmd_test_class().command_string == "AT+CMD"  # default mode is "execute"
    assert at_cmd_test_class(operation=cmd_mode).command_string == expected_cmd_string


def test_at_cmd_string_extended_with_params_when_additional_params_in_execute_mode_provided():
    from moler.cmd.at.at import AtCmd

    class AtCmdWithArgs(AtCmd):
        def __init__(self, connection=None, operation="execute", context_id=None, option=None, action=None):
            super(AtCmdWithArgs, self).__init__(connection, operation)
            self.set_at_command_string(command_base_string="AT+CMD",
                                       execute_params=[('context_id', context_id), ('option', option), ('action', action)])

        def parse_command_output(self):
            self.set_result("result")

    at_cmd = AtCmdWithArgs()
    assert at_cmd.command_string == "AT+CMD"

    at_cmd = AtCmdWithArgs(context_id=5)
    assert at_cmd.command_string == "AT+CMD=5"

    at_cmd = AtCmdWithArgs(context_id=2, option="off", action='reset')
    assert at_cmd.command_string == "AT+CMD=2,off,reset"


def test_calling_at_cmd_raises_AtCommandFailure_when_regular_ERROR_in_at_cmd_output_occurred(buffer_connection, at_cmd_test_class):
    from moler.cmd.at.at import AtCommandFailure
    buffer_connection.remote_inject_response(["at+cmd\nERROR\n"])
    at_cmd = at_cmd_test_class(connection=buffer_connection.moler_connection)
    with pytest.raises(AtCommandFailure) as error:
        at_cmd()
    assert str(error.value) == "ERROR"


def test_calling_at_cmd_raises_AtCommandFailure_with_error_msg_from_at_cmd_output(buffer_connection, at_cmd_test_class):
    from moler.cmd.at.at import AtCommandFailure
    buffer_connection.remote_inject_response(["at+cmd\n+CME   ERROR: no connection to phone\n"])
    at_cmd = at_cmd_test_class(connection=buffer_connection.moler_connection)
    with pytest.raises(AtCommandFailure) as error:
        at_cmd()
    assert str(error.value) == "ERROR: no connection to phone"


def test_at_cmd_raises_AtCommandModeNotSupported_when_instantiated_in_incorrect_mode(at_cmd_test_class):
    from moler.cmd.at.at import AtCommandModeNotSupported
    with pytest.raises(AtCommandModeNotSupported) as error:
        at_cmd_test_class(operation="magic_mode")
