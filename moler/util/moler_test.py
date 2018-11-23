# -*- coding: utf-8 -*-
"""
Utility/common code of library.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import logging
from functools import partial
from functools import wraps
from types import FunctionType, MethodType

from moler.connection_observer import ConnectionObserver
from moler.exceptions import MolerException
from moler.exceptions import MolerStatusException


class MolerTest(object):
    _was_error = False
    _was_steps_end = False
    _logger = logging.getLogger("moler")

    @staticmethod
    def steps_end():
        MolerTest._was_steps_end = True

    @staticmethod
    def error(msg, raise_exception=False):
        MolerTest._was_error = True
        MolerTest._logger.error(msg, extra={'moler_error': True})
        if raise_exception:
            raise MolerException(msg)

    @staticmethod
    def info(msg):
        MolerTest._logger.info(msg)

    @staticmethod
    def _steps_start():
        unraised_exceptions = ConnectionObserver.get_unraised_exceptions(True)

        if unraised_exceptions:
            err_msg = "There were some errors in previous Moler test. Please check Moler logs for details.\n"
            for unraised_exception in unraised_exceptions:
                err_msg = "{}{}\n".format(err_msg, unraised_exception)
            MolerTest.error(err_msg)

        MolerTest._was_steps_end = False

    @staticmethod
    def _check_exceptions_occured(caught_exception=None):
        unraised_exceptions = ConnectionObserver.get_unraised_exceptions(True)
        occured_exceptions = list()
        for unraised_exception in unraised_exceptions:
            occured_exceptions.append(unraised_exception)
            MolerTest.error("Unhandled exception: '{}'".format(unraised_exception))
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
        if err_msg:
            MolerTest.error(err_msg)
            MolerTest._was_error = False
            raise MolerStatusException(err_msg, occured_exceptions)

    @staticmethod
    def _check_steps_end():
        if not MolerTest._was_steps_end:
            err_msg = "Method steps_end() was not called.\n"
            MolerTest.error(err_msg)
            MolerTest._was_error = False
            raise MolerStatusException(err_msg)

    @staticmethod
    def raise_background_exceptions(decorated="function", check_steps_end=False):
        if callable(decorated):
            # direct decoration
            return MolerTest._decorate(decorated, check_steps_end=check_steps_end)
        else:
            return partial(MolerTest._decorate, check_steps_end=check_steps_end)

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
