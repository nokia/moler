# -*- coding: utf-8 -*-
"""
Testing resources for tests of AT commands.
"""
from pytest import fixture, yield_fixture

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


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


