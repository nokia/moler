# -*- coding: utf-8 -*-
"""
Testing resources for tests of AT commands.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

from pytest import fixture, yield_fixture
import os
import logging

import moler.config.loggers
from moler.helpers import instance_id

# plugins to let us see (in moler logs) where we are in testing


def pytest_runtest_protocol(item, nextitem):
    logger = logging.getLogger("moler")
    logger.propagate = False
    logger.log(level=moler.config.loggers.TEST_CASE, msg=item.nodeid)


def pytest_runtest_logreport(report):
    logger = logging.getLogger("moler")
    logger.propagate = False
    logger.log(level=moler.config.loggers.TEST_CASE,
               msg="TC {} [{}]".format(str(report.when).upper(),
                                       str(report.outcome).upper()))


# --------------------------- cmd_at and cmd_at_get_imsi resources ---------------------------
@yield_fixture
def buffer_connection():
    from moler.io.raw.memory import ThreadedFifoBuffer
    from moler.connection import ObservableConnection
    from moler.config.loggers import configure_device_logger

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
    configure_device_logger(moler_conn.name)
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
moler.config.loggers.raw_logs_active = True
moler.config.loggers.configure_debug_level()
moler.config.loggers.configure_moler_main_logger()
moler.config.loggers.configure_runner_logger(runner_name="thread-pool")


# --------------------------- test/test_cmds_doc.py resources ---------------------------
@fixture
def fake_cmd():
    class FakeCommand:
        def __call__(self, fake):
            pass
    return FakeCommand


@fixture
def nice_cmd():
    from moler.command import Command

    class NiceCommand(Command):
        def __init__(self, nice='', connection=None):
            super(NiceCommand, self).__init__(connection=connection)
            self.nice = nice

        def data_received(self, data):
            if self.nice == 'nice':
                self.set_result({'nice': 'nice'})

        def __call__(self, timeout=None, *args, **kwargs):
            self.set_result({'nice': self.nice})
            return {'nice': self.nice}

    return NiceCommand


COMMAND_OUTPUT_ver_nice = """
'nice'
"""

COMMAND_KWARGS_ver_nice = {}

COMMAND_RESULT_ver_nice = {
    'nice': 'nice'
}
