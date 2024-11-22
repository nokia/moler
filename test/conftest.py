# -*- coding: utf-8 -*-
"""
Testing resources for tests of AT commands.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2024, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

from pytest import fixture
import os
import logging
import psutil
import threading
import platform

import moler.config.loggers
from moler.util.devices_SM import get_memory_device_connection
import moler.connection_factory  # will load builtin connections and default variants
from moler.moler_connection_for_single_thread_runner import MolerConnectionForSingleThreadRunner


current_process = psutil.Process()
if platform.system() == 'Linux':
    (max_open_files_limit_soft, max_open_files_limit_hard) = current_process.rlimit(psutil.RLIMIT_NOFILE)
else:
    # https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/setmaxstdio?view=vs-2019
    (max_open_files_limit_soft, max_open_files_limit_hard) = (510, 512)  # TODO: any way on Win?


def system_resources_usage():
    if platform.system() == 'Windows':
        ofiles = current_process.open_files()
        osockets = current_process.connections(kind="all")
        curr_fds_open = len(ofiles) + len(osockets)  # TODO: any better way on Win?
    else:
        curr_fds_open = current_process.num_fds()
    curr_threads_nb = threading.active_count()
    return curr_fds_open, curr_threads_nb


def system_resources_usage_msg(curr_fds_open, curr_threads_nb):
    msg = "RESOURCES USAGE: {}/{} FDs OPEN, {} threads active.".format(curr_fds_open, max_open_files_limit_soft,
                                                                       curr_threads_nb)
    return msg


def check_system_resources_limit(logger):
    # The number of file descriptors currently opened by this process
    curr_fds_open = current_process.num_fds()
    if curr_fds_open > max_open_files_limit_soft - 10:
        prefix = "!!! ALMOST REACHED"
        msg = f"{prefix} MAX OPEN FILES LIMIT ({max_open_files_limit_soft}). Now {curr_fds_open} FDs open"
        logger.warning(msg)
        raise Exception(msg)

# plugins to let us see (in moler logs) where we are in testing


resources_stats = {'START': (0, 0), 'SETUP': (0, 0), 'CALL': (0, 0), 'TEARDOWN': (0, 0)}


def pytest_runtest_protocol(item, nextitem):
    resources_stats['START'] = system_resources_usage()
    resources_stats['SETUP'] = resources_stats['CALL'] = resources_stats['TEARDOWN'] = (0, 0)
    logger = logging.getLogger("moler")
    logger.propagate = False
    resources_usage_msg = system_resources_usage_msg(*resources_stats['START'])
    logger.log(level=moler.config.loggers.TEST_CASE, msg=f"{item.nodeid} - {resources_usage_msg}")
    check_system_resources_limit(logger)


def pytest_runtest_logreport(report):
    logger = logging.getLogger("moler")
    logger.propagate = False
    when = str(report.when).upper()
    resources_stats[when] = system_resources_usage()
    resources_usage_msg = system_resources_usage_msg(*resources_stats[when])
    msg = f"TC {when} [{str(report.outcome).upper()}] - {resources_usage_msg}"
    logger.log(level=moler.config.loggers.TEST_CASE, msg=msg)
    if when == 'TEARDOWN':
        logger.log(level=moler.config.loggers.TEST_CASE, msg=str(resources_stats))
        initial_fds = resources_stats['START'][0]
        final_fds = resources_stats['TEARDOWN'][0]
        initial_threads = resources_stats['START'][1]
        final_threads = resources_stats['TEARDOWN'][1]
        if (final_fds > initial_fds) or (final_threads > initial_threads):
            err_msg = " !!! LEAKING RESOURCES: {} -> {} FDs, {} -> {} threads".format(initial_fds, final_fds,
                                                                                 initial_threads, final_threads)
            logger.log(level=logging.ERROR, msg=err_msg)
    check_system_resources_limit(logger)


# --------------------------- cmd_at and cmd_at_get_imsi resources ---------------------------
@fixture
def buffer_connection():
    from moler.io.raw.memory import ThreadedFifoBuffer
    from moler.threaded_moler_connection import ThreadedMolerConnection
    from moler.config.loggers import configure_device_logger

    class RemoteConnection(ThreadedFifoBuffer):
        def remote_inject_response(self, input_strings, delay=0.0):
            """
            Simulate remote endpoint that sends response.
            Response is given as strings.
            """
            in_bytes = [data.encode("utf-8") for data in input_strings]
            self.inject_response(in_bytes, delay)

        def remote_inject_line(self, line, add_newline=True, delay=0.0):
            """
            Simulate remote endpoint that sends full line.
            Line is given as string.
            """
            if add_newline:
                if not line.endswith("\n"):
                    line = f"{line}\n"
            line_as_bytes = line.encode("utf-8")
            self.inject([line_as_bytes], delay)

        def get_runner(self):
            """Get default runner for this connection."""
            return None

    # moler_conn = ThreadedMolerConnection(encoder=lambda data: data.encode("utf-8"),
    #                                      decoder=lambda data: data.decode("utf-8"),
    #                                      name="buffer")
    moler_conn = MolerConnectionForSingleThreadRunner(encoder=lambda data: data.encode("utf-8"),
                                                      decoder=lambda data: data.decode("utf-8"),
                                                      name="buffer")
    ext_io_in_memory = RemoteConnection(moler_connection=moler_conn,
                                        echo=False)  # we don't want echo on connection
    configure_device_logger(moler_conn.name)
    # all tests assume working with already open connection
    with ext_io_in_memory.open():  # open it (autoclose by context-mngr)
        yield ext_io_in_memory


# actions during import:
os.environ['MOLER_DEBUG_LEVEL'] = 'TRACE'  # to have all debug details of tests
moler.config.loggers.raw_logs_active = True
moler.config.loggers.configure_debug_level()
moler.config.loggers.set_write_mode(mode="write")
moler.config.loggers.configure_moler_main_logger()
moler.config.loggers.configure_runner_logger(runner_name="thread-pool")
moler.config.loggers.configure_runner_logger(runner_name="asyncio")


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

        def data_received(self, data, recv_time):
            if self.nice == 'nice':
                self.set_result({'nice': 'nice'})

        def __call__(self, timeout=None, *args, **kwargs):
            self.set_result({'nice': self.nice})
            return {'nice': self.nice}

    return NiceCommand


# --------------------------- test/device/test_SM_DEVICE_NAME.py resources ---------------------------
@fixture
def device_connection():
    ext_io_in_memory = get_memory_device_connection()
    # all tests assume working with already open connection
    with ext_io_in_memory:  # open it (autoclose by context-mngr)
        yield ext_io_in_memory


COMMAND_OUTPUT_ver_nice = """
'nice'
"""

COMMAND_KWARGS_ver_nice = {}

COMMAND_RESULT_ver_nice = {
    'nice': 'nice'
}
