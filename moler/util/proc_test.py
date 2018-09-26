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


class ProcTestWrapper(object):
    start_time = 0
    was_error = False
    was_steps_end = False
    logger = logging.getLogger("moler")

    @staticmethod
    def steps_start():
        ProcTestWrapper.was_steps_end = False

    @staticmethod
    def steps_end():
        ProcTestWrapper.was_steps_end = True

    @staticmethod
    def final_check():
        # Checks exceptions since last call final_check
        exceptions = ConnectionObserver.get_active_exceptions_in_time(ProcTestWrapper.start_time)
        for exception in exceptions:
            ProcTestWrapper.log_error("Unhandled exception: '{}'".format(exception))
        ProcTestWrapper.start_time = time.time()
        was_error_in_last_execution = ProcTestWrapper.was_error
        ProcTestWrapper.was_error = False
        assert ProcTestWrapper.was_steps_end is True
        assert was_error_in_last_execution is False

    @staticmethod
    def log_error(msg):
        ProcTestWrapper.status = False
        ProcTestWrapper.logger.error(msg)

    @staticmethod
    def log(msg):
        ProcTestWrapper.logger.info(msg)


def log_error(msg):
    ProcTestWrapper.log_error(msg)


def log(msg):
    ProcTestWrapper.log(msg)


def steps_end():
    ProcTestWrapper.steps_end()


def wrapper(method):
    @wraps(method)
    def wrapped(*args, **kwrds):
        class_name = args[0].__class__.__name__
        method_name = method.__name__


        ProcTestWrapper.steps_start()
        start_time = datetime.datetime.now()
        print("START Method: {}.{} -> {}".format(class_name, method_name, start_time))

        result = method(*args, **kwrds)

        stop_time = datetime.datetime.now()
        print("END Method: {}.{} -> {}".format(class_name, method_name, stop_time))
        ProcTestWrapper.final_check()

        return result


    return wrapped


class MetaProcTest(type):
    def __new__(meta, class_name, bases, classDict):
        newClassDict = {}
        for attributeName, attribute in classDict.items():
            if attributeName.startswith("test"):
                if isinstance(attribute, FunctionType):
                    # replace it with a wrapped version
                    attribute = wrapper(attribute)
            newClassDict[attributeName] = attribute
        return type.__new__(meta, class_name, bases, newClassDict)


class ProcTest(MetaProcTest('ProcTest', (object,), {})):
    pass
