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
from types import FunctionType, MethodType

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
        print("log_error: '{}'".format(msg))
        MolerTest._logger.error(msg)
        if raise_exception:
            raise MolerException(msg)

    @staticmethod
    def log(msg):
        MolerTest._logger.info(msg)

    @staticmethod
    def _steps_start():
        MolerTest._was_steps_end = False

    @staticmethod
    def _final_check(caught_exception=None, check_steps_end=True):
        print("_final_check start {}:{}:'{}'".format(check_steps_end, MolerTest._was_error, caught_exception))
        # Checks exceptions since last call final_check
        final_check_time = time.time()
        exceptions = ConnectionObserver.get_active_exceptions_in_time(MolerTest._last_check_time, time.time(), True)
        for exception in exceptions:
            MolerTest.log_error("Unhandled exception: '{}'".format(exception))
        MolerTest._last_check_time = final_check_time
        was_error_in_last_execution = MolerTest._was_error
        MolerTest._was_error = False
        print("_final_check before asserts")
        print("Leaving _final_check1: .was_error{}, check_steps_end:{}, _was_steps_end:{}".format(MolerTest._was_error,
                                                                                                  check_steps_end,
                                                                                                  MolerTest._was_steps_end))
        if check_steps_end:
            assert MolerTest._was_steps_end is True
        print("Leaving _final_check2: {}".format(MolerTest._was_error))
        assert was_error_in_last_execution is False
        # assert caught_exception is None
        print("Leaving _final_check3: {}".format(MolerTest._was_error))

    @staticmethod
    def moler_raise_background_exceptions():
        def decorate(cls):
            for attributeName, attribute in cls.__dict__.items():
                if attributeName.startswith("test"):
                    if isinstance(attribute, (FunctionType, MethodType)):
                        setattr(cls, attributeName, MolerTest.wrapper(attribute, False))
            return cls

        return decorate

    @staticmethod
    def moler_raise_background_exceptions_steps_end():
        def decorate(cls):
            for attributeName, attribute in cls.__dict__.items():
                if attributeName.startswith("test"):
                    if isinstance(attribute, (FunctionType, MethodType)):
                        setattr(cls, attributeName, MolerTest.wrapper(attribute, True))
            return cls

        return decorate

    @staticmethod
    def wrapper(method, check_steps_end):
        if hasattr(method, '_already_decorated') and method._already_decorated:
            return method

        @wraps(method)
        def wrapped(*args, **kwargs):
            print("\nStart of wrapped...{}".format(method))
            MolerTest._steps_start()
            caught_exception = None
            try:
                result = method(*args, **kwargs)
            except Exception as exc:
                caught_exception = exc
            finally:
                MolerTest._final_check(caught_exception, check_steps_end)
            return result

        wrapped._already_decorated = True
        return wrapped
