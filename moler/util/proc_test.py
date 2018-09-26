# -*- coding: utf-8 -*-
"""
Utility/common code of library.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import logging
import time
from functools import wraps
from types import FunctionType

from moler.connection_observer import ConnectionObserver
from moler.exceptions import MolerException


class MolerTest(object):
    _last_check_time = 0
    _was_error = False
    _was_steps_end = False
    _logger = logging.getLogger("moler")

    @staticmethod
    def steps_end():
        MolerTest._was_steps_end = True

    @staticmethod
    def log_error(msg, raise_exception=False):
        MolerTest._was_error = True
        MolerTest._logger.error(msg)
        if raise_exception:
            raise MolerException(msg)

    @staticmethod
    def log(msg):
        MolerTest._logger.info(msg)

    @staticmethod
    def steps_start():
        MolerTest._was_steps_end = False

    @staticmethod
    def final_check():
        # Checks exceptions since last call final_check
        final_check_time = time.time()
        exceptions = ConnectionObserver.get_active_exceptions_in_time(MolerTest._last_check_time)
        for exception in exceptions:
            MolerTest.log_error("Unhandled exception: '{}'".format(exception))
        MolerTest._last_check_time = final_check_time
        was_error_in_last_execution = MolerTest._was_error
        MolerTest._was_error = False
        assert MolerTest._was_steps_end is True
        assert was_error_in_last_execution is False


def wrapper(method):
    @wraps(method)
    def wrapped(*args, **kwrds):
        # class_name = args[0].__class__.__name__
        # method_name = method.__name__
        MolerTest.steps_start()
        # start_time = datetime.datetime.now()
        result = method(*args, **kwrds)
        # stop_time = datetime.datetime.now()
        MolerTest.final_check()
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
