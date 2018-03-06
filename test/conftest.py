# -*- coding: utf-8 -*-
"""
Testing resources for tests of AT commands.
"""
from pytest import fixture, yield_fixture

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


# --------------------------- cmd_at and cmd_at_get_imsi resources ---------------------------
@yield_fixture
def buffer_connection():
    from moler.io.raw.memory import ThreadedFifoBuffer
    from moler.connection import ObservableConnection

    class RemoteConnection(ThreadedFifoBuffer):
        def remote_inject_response(self, input_strings, delay=0.0):
            """
            Simulate remote endpoint that sends response.
            Response is given as strings.
            """
            in_bytes = [data.encode("utf-8") for data in input_strings]
            self.inject_response(in_bytes, delay)

    moler_conn = ObservableConnection(encoder=lambda data: data.encode("utf-8"),
                                      decoder=lambda data: data.decode("utf-8"))
    ext_io_in_memory = RemoteConnection(moler_connection=moler_conn,
                                        echo=False)  # we don't want echo on connection
    # all tests assume working with already open connection
    with ext_io_in_memory:  # open it (autoclose by context-mngr)
        yield ext_io_in_memory


@fixture
def at_cmd_test_class():
    from moler.cmd.at.at import AtCmd

    class AtCmdTest(AtCmd):
        def __init__(self, connection=None, operation="execute"):
            super(AtCmdTest, self).__init__(connection, operation)
            self.set_at_command_string("AT+CMD")

        def parse_command_output(self):
            self.set_result("result")

    return AtCmdTest
