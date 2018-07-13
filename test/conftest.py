# -*- coding: utf-8 -*-
"""
Testing resources for tests of AT commands.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

from pytest import fixture, yield_fixture
import os
import logging

import moler.config.loggers
from moler.helpers import instance_id

# plugins to let us see (in moler logs) where we are in testing


def pytest_runtest_protocol(item, nextitem):
    logger = logging.getLogger("moler")
    logger.log(level=moler.config.loggers.TEST_CASE, msg=item.nodeid)


def pytest_runtest_logreport(report):
    logger = logging.getLogger("moler")
    logger.log(level=moler.config.loggers.TEST_CASE,
               msg="TC {} [{}]".format(str(report.when).upper(),
                                       str(report.outcome).upper()))


# --------------------------- cmd_at and cmd_at_get_imsi resources ---------------------------
@yield_fixture
def buffer_connection():
    from moler.io.raw.memory import ThreadedFifoBuffer
    from moler.connection import ObservableConnection
    from moler.config.loggers import configure_connection_logger

    class RemoteConnection(ThreadedFifoBuffer):
        def remote_inject_response(self, input_strings, delay=0.0):
            """
            Simulate remote endpoint that sends response.
            Response is given as strings.
            """
            in_bytes = [data.encode("utf-8") for data in input_strings]
            self.inject_response(in_bytes, delay)

    moler_conn = ObservableConnection(encoder=lambda data: data.encode("utf-8"),
                                      decoder=lambda data: data.decode("utf-8"),
                                      name="buffer")
    ext_io_in_memory = RemoteConnection(moler_connection=moler_conn,
                                        echo=False)  # we don't want echo on connection
    configure_connection_logger(moler_conn.name)
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


# actions during import:
os.environ['MOLER_DEBUG_LEVEL'] = 'TRACE'  # to have all debug details of tests
moler.config.loggers.configure_debug_level()
moler.config.loggers.configure_moler_main_logger()
moler.config.loggers.configure_runner_logger(runner_name="thread-pool")
