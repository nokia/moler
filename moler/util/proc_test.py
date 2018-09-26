# -*- coding: utf-8 -*-
"""
Utility/common code of library.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import datetime
import time
from functools import wraps
from types import FunctionType
from moler.connection_observer import ConnectionObserver
import logging


class ProcTest(object):
    last_check_time = 0
    was_error = False
    was_steps_end = False
    logger = logging.getLogger("moler")

    @staticmethod
    def steps_start():
        ProcTest.was_steps_end = False

    @staticmethod
    def steps_end():
        ProcTest.was_steps_end = True

    @staticmethod
    def final_check():
        # Checks exceptions since last call final_check
        final_check_time = time.time()
        exceptions = ConnectionObserver.get_active_exceptions_in_time(ProcTest.last_check_time)
        for exception in exceptions:
            ProcTest.log_error("Unhandled exception: '{}'".format(exception))
        ProcTest.last_check_time = final_check_time
        was_error_in_last_execution = ProcTest.was_error
        ProcTest.was_error = False
        assert ProcTest.was_steps_end is True
        assert was_error_in_last_execution is False

    @staticmethod
    def log_error(msg):
        ProcTest.was_error = True
        ProcTest.logger.error(msg)

    @staticmethod
    def log(msg):
        ProcTest.logger.info(msg)


def log_error(msg):
    ProcTest.log_error(msg)


def log(msg):
    ProcTest.log(msg)


def steps_end():
    ProcTest.steps_end()


def wrapper(method):
    @wraps(method)
    def wrapped(*args, **kwrds):
        class_name = args[0].__class__.__name__
        method_name = method.__name__
        ProcTest.steps_start()
        start_time = datetime.datetime.now()
        result = method(*args, **kwrds)
        stop_time = datetime.datetime.now()

        ProcTest.final_check()
        return result

    return wrapped


def moler_test_status():
    def decorate(cls):
        for attributeName, attribute in cls.__dict__.items():
            if attributeName.startswith("test"):
                if isinstance(attribute, FunctionType):
                    setattr(cls, attributeName, wrapper(attribute))
        return cls

    return decorate
