# -*- coding: utf-8 -*-
"""
Utility/common code of library.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import logging
import time
from functools import partial
from functools import wraps
from types import FunctionType, MethodType

from moler.connection_observer import ConnectionObserver
from moler.exceptions import MolerException
from moler.exceptions import MolerStatusException


class MolerTest(object):

    @staticmethod
    def steps_end():
        """
        You should call this function at the end of your test code with Moler.
        :return: Nothing
        """
        MolerTest._was_steps_end = True

    @staticmethod
    def error(msg, raise_exception=False):
        """
        Makes an error (fail the test) and (optional) continue the test flow.
        :param msg: Message to show.
        :param raise_exception: If True then raise an exception, if False then only show msg and mark error in logs.
        :return: Nothing.
        """
        MolerTest._list_of_errors.append(msg)
        MolerTest._error(msg, raise_exception)

    @staticmethod
    def info(msg):
        """
        Shows the message
        :param msg: Message to show.
        :return: Nothing.
        """
        MolerTest._logger.info(msg)

    @staticmethod
    def warning(msg):
        """
        Shows the message as warning.
        :param msg: Message to show.
        :return: Nothing
        """
        MolerTest._logger.warning(msg)

    @staticmethod
    def sleep(seconds):
        """
        Add sleep functionality
        TODO: add support to asyncio when runner ready
        :param seconds: Time to sleep (in seconds)
        :return:
        """
        MolerTest.info("Sleep for {:.2f} seconds.".format(seconds))
        time.sleep(seconds)

    @staticmethod
    def raise_background_exceptions(decorated="function", check_steps_end=False):
        """
        Decorates the function, method or class.
        :param decorated: Function, method or class to decorate.
        :param check_steps_end: If True then check if steps_end was called before return the method, if False then do
         not check
        :return: Decorated callable
        """
        if callable(decorated):
            # direct decoration
            return MolerTest._decorate(decorated, check_steps_end=check_steps_end)
        else:
            return partial(MolerTest._decorate, check_steps_end=check_steps_end)

    # No public methods and fields below:

    _was_error = False
    _was_steps_end = False
    _logger = logging.getLogger("moler")
    _list_of_errors = list()

    @staticmethod
    def _error(msg, raise_exception=False):
        MolerTest._was_error = True
        MolerTest._logger.error(msg, extra={'moler_error': True})
        if raise_exception:
            raise MolerException(msg)

    @staticmethod
    def _steps_start():
        err_msg = ""
        unraised_exceptions = ConnectionObserver.get_unraised_exceptions(True)
        if MolerTest._list_of_errors:
            err_msg += "There were errors in previous Moler test. Please check Moler logs for details. List of them:\n"
            for msg in MolerTest._list_of_errors:
                MolerTest._error("    {}\n".format(msg))
        if unraised_exceptions:
            err_msg += "There were unhandled exceptions in previous Moler test. Please check Moler logs for details.\n"
            for unraised_exception in unraised_exceptions:
                err_msg = "    {}{}\n".format(err_msg, unraised_exception)
            MolerTest._error(err_msg)
        MolerTest._list_of_errors = list()  # clean the list for new test

        MolerTest._was_steps_end = False

    @staticmethod
    def _check_exceptions_occured(caught_exception=None):
        unraised_exceptions = ConnectionObserver.get_unraised_exceptions(True)
        occured_exceptions = list()
        for unraised_exception in unraised_exceptions:
            occured_exceptions.append(unraised_exception)
            MolerTest._error("Unhandled exception: '{}'".format(unraised_exception))
        if caught_exception:
            occured_exceptions.append(caught_exception)

        was_error_in_last_execution = MolerTest._was_error
        err_msg = ""

        if was_error_in_last_execution:
            err_msg += "There were error messages in Moler execution. Please check Moler logs for details.\n"
        if len(occured_exceptions) > 0:
            err_msg += "There were unhandled exceptions in Moler.\n"
            for exc in occured_exceptions:
                try:
                    import traceback
                    exc_traceback = ' '.join(traceback.format_tb(exc.__traceback__))
                    err_msg += "{}{}".format(exc_traceback, repr(exc))
                except AttributeError:
                    err_msg += repr(exc)
        if len(MolerTest._list_of_errors) > 0:
            err_msg += "There were error messages in Moler execution."
        if err_msg:
            MolerTest._error(err_msg)
            MolerTest._was_error = False
            error_msgs = MolerTest._list_of_errors
            MolerTest._list_of_errors = list()
            raise MolerStatusException(err_msg, occured_exceptions, error_msgs)

    @staticmethod
    def _check_steps_end():
        if not MolerTest._was_steps_end:
            err_msg = "Method steps_end() was not called.\n"
            MolerTest._error(err_msg)
            MolerTest._was_error = False
            raise MolerStatusException(err_msg)

    @staticmethod
    def _decorate(obj=None, check_steps_end=False):
        # check that decorated function is not statimethod or classmethod
        if not obj:
            raise MolerStatusException("Decorator for 'staticmethod' or 'classmethod' not implemented yet.",
                                       [MolerException()])

        if hasattr(obj, "__dict__"):
            if obj.__dict__.items():
                for attributeName in dir(obj):
                    if attributeName == "_already_decorated":
                        break

                    attribute = getattr(obj, attributeName)

                    if not attributeName.startswith("_"):
                        if isinstance(attribute, (FunctionType, MethodType)):
                            setattr(obj, attributeName, MolerTest._wrapper(attribute, check_steps_end))
            else:
                obj = MolerTest._wrapper(obj, True)
        else:
            raise MolerStatusException("No '__dict__' in decorated object.", [MolerException()])

        return obj

    @staticmethod
    def _wrapper(method, check_steps_end):
        if hasattr(method, '_already_decorated') and method._already_decorated:
            return method

        @wraps(method)
        def wrapped(*args, **kwargs):
            MolerTest._steps_start()
            caught_exception = None
            try:
                result = method(*args, **kwargs)
            except Exception as exc:
                caught_exception = exc
            finally:
                MolerTest._check_exceptions_occured(caught_exception)
                if check_steps_end:
                    MolerTest._check_steps_end()
            return result

        wrapped._already_decorated = True
        return wrapped
