# -*- coding: utf-8 -*-
"""
Utility/common code of library.
"""

__author__ = "Grzegorz Latuszek, Marcin Usielski, Michal Ernst, Tomasz Krol"
__copyright__ = "Copyright (C) 2018-2025, Nokia"
__email__ = "grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com, tomasz.krol@nokia.com"

import gc
import inspect
import logging
import os
import pprint
import signal
import time
import traceback
from functools import partial, wraps
from types import FunctionType, MethodType

from moler.config.loggers import get_error_log_stack, switch_debug_log_visibility
from moler.connection_observer import ConnectionObserver
from moler.exceptions import ExecutionException, MolerException


class MolerTest:
    @classmethod
    def steps_end(cls):
        """
        You should call this function at the end of your test code with Moler.

        :return: None
        """
        cls._was_steps_end = True

    @classmethod
    def error(cls, msg, raise_exception=False, dump=None):
        """
        Makes an error (fail the test) and (optional) continue the test flow.

        :param msg: Message to show.
        :param raise_exception: If True then raise an exception (if not in try except block then test will be
         terminated), if False then only show msg and mark error in logs.
        :param dump: If defined then dump object.
        :return: None
        """
        cls._list_of_errors.append(msg)
        cls._error(msg, raise_exception, dump)

    @classmethod
    def info(cls, msg, dump=None):
        """
        Shows the message.

        :param msg: Message to show.
        :param dump: If defined then dump object.
        :return: None
        """
        msg = cls._get_string_message(msg, dump, None)
        cls._logger.info(msg)

    @classmethod
    def warning(cls, msg, dump=None):
        """
        Shows the message as warning.

        :param msg: Message to show.
        :param dump: If defined then dump object.
        :return: None
        """
        msg = cls._get_string_message(msg, dump, None)
        cls._logger.warning(msg)

    @classmethod
    def stop_python(cls, force=False):
        """
        Stops current Python.

        :return: None
        """
        cls.info("Python will be closed by user request.")
        pid = os.getpid()
        if force:
            os.kill(pid, signal.SIGKILL)
        os.kill(pid, signal.SIGINT)

    @classmethod
    def _dump(cls, obj):
        """
        Dumping objet to moler log.

        :param obj: Object to dump.
        :return: Dumped object as string
        """
        msg_str = pprint.pformat(obj, indent=1)
        return msg_str

    @classmethod
    def _get_string_message(cls, msg, dump, caller_msg):
        if dump is not None:
            dump_str = cls._dump(dump)
            msg = f"{msg}\n{dump_str}"
        if caller_msg:
            msg = f"{msg}\n{caller_msg}"

        return msg

    @classmethod
    def sleep(cls, seconds, quiet=False):
        """
        Add sleep functionality.

        TODO: add support to asyncio when runner ready
        :param seconds: Time to sleep (in seconds)
        :param quiet: If True then no info to log about sleeping, if False then sleep info will be logged
        :return:
        """
        if not quiet:
            cls.info(f"Sleep for {seconds:.2f} seconds.")
        time.sleep(seconds)

    @classmethod
    def raise_background_exceptions(cls, decorated="function", check_steps_end=False):
        """
        Decorates the function, method or class.

        :param decorated: Function, method or class to decorate.
        :param check_steps_end: If True then check if steps_end was called before return the method, if False then do
         not check
        :return: Decorated callable
        """
        if callable(decorated):
            # direct decoration
            return cls._decorate(decorated, check_steps_end=check_steps_end)
        else:
            return partial(cls._decorate, check_steps_end=check_steps_end)

    @classmethod
    def disable_debug_log(cls):
        """
        Disable debug log.

        :return: None
        """
        switch_debug_log_visibility(disable=True)

    @classmethod
    def enable_debug_log(cls):
        """
        Enable debug log.

        :return: None
        """
        switch_debug_log_visibility(disable=False)

    # No public methods and fields below:

    _was_error = False
    _was_steps_end = False
    _logger = logging.getLogger("moler")
    _list_of_errors = []

    @classmethod
    def _error(cls, msg, raise_exception=False, dump=None):
        caller_msg = cls._caller_info()
        cls._was_error = True
        msg = cls._get_string_message(msg, dump, caller_msg)
        cls._logger.error(msg, extra={"moler_error": True})

        if raise_exception:
            raise MolerException(msg)

    @classmethod
    def _caller_info(cls):
        full_stack = get_error_log_stack()
        stack = inspect.stack()
        msg = ""
        for fi in stack:
            filename = fi[1]
            if filename == __file__:
                continue
            function_name = fi[3]
            line_no = fi[2]
            file_abs_path = os.path.abspath(filename)
            msg = f"{msg}    from {function_name} at {file_abs_path}:{line_no}"
            if full_stack:
                msg = f"{msg}\n"
            else:
                break
        return msg

    @classmethod
    def _steps_start(cls):
        err_msg = cls._prepare_err_msg(None)
        cls._list_of_errors = []  # clean the list for new test
        cls._was_error = False
        cls._was_steps_end = False
        if err_msg:
            prefix = (
                "Moler caught some error messages during execution. Please check Moler logs for details."
                " List of them:\n"
            )
            err_msg = f"{prefix} {err_msg}"
            cls._error(err_msg)

    @classmethod
    def _prepare_err_msg(cls, caught_exception):
        was_error_in_last_execution = cls._was_error
        err_msg = ""
        get_traceback = False

        unraised_exceptions = ConnectionObserver.get_unraised_exceptions(True)
        occured_exceptions = []
        for unraised_exception in unraised_exceptions:
            occured_exceptions.append(unraised_exception)
        if caught_exception:
            occured_exceptions.append(caught_exception)

        if was_error_in_last_execution:
            err_msg += "Moler caught some error messages during execution. Please check Moler logs for details.\n"
        if len(occured_exceptions) > 0:
            err_msg += "There were unhandled exceptions from test caught by Moler.\n"
            for i, exc in enumerate(occured_exceptions, 1):
                if hasattr(exc, "__traceback__"):
                    exc_traceback = " ".join(traceback.format_tb(exc.__traceback__))
                    err_msg += f"  ({i}) {exc_traceback}{repr(exc)}\n"
                else:
                    get_traceback = True
            if get_traceback:
                err_msg += f"  {cls._get_tracebacks()}\n"

        if len(cls._list_of_errors) > 0:
            err_msg += "Moler caught some error messages during execution:\n"

            for i, msg in enumerate(cls._list_of_errors, 1):
                err_msg += f"  {i}) >>{msg}<<\n"

        return err_msg

    @classmethod
    def _get_tracebacks(cls):
        return traceback.format_exc()

    @classmethod
    def _check_exceptions_occured(cls, caught_exception=None):
        err_msg = cls._prepare_err_msg(caught_exception)

        if err_msg:
            cls._error(err_msg)
            cls._was_error = False
            cls._list_of_errors = []
            raise ExecutionException(err_msg)

    @classmethod
    def _check_steps_end(cls):
        if not cls._was_steps_end:
            err_msg = "Method 'steps_end()' was not called or parameter 'check_steps_end' was not set properly.\n."
            cls._error(err_msg)
            cls._was_error = False
            raise ExecutionException(err_msg)

    @classmethod
    def _decorate(cls, obj=None, check_steps_end=False):
        # check that decorated function is not staticmethod or classmethod
        if not obj:
            raise ExecutionException(
                "Decorator for 'staticmethod' or 'classmethod' not implemented yet.",
            )
        desc = next(
            (desc for desc in (staticmethod, classmethod) if isinstance(obj, desc)),
            None,
        )
        if desc:
            raise ExecutionException(
                "Use decorator '@staticmethod' or '@classmethod' as uppermost."
            )

        if hasattr(obj, "__dict__"):
            if obj.__dict__.items():
                for attributeName in dir(obj):
                    if attributeName == "_already_decorated":
                        break

                    attribute = getattr(obj, attributeName)

                    if not attributeName.startswith("_"):
                        if isinstance(attribute, (FunctionType, MethodType)):
                            setattr(
                                obj,
                                attributeName,
                                cls._wrapper(
                                    attribute, check_steps_end=check_steps_end
                                ),
                            )
            else:
                obj = cls._wrapper(obj, check_steps_end=check_steps_end)
        else:
            raise ExecutionException("No '__dict__' in decorated object.")

        return obj

    @classmethod
    def _wrapper(cls, method, check_steps_end):
        if hasattr(method, "_already_decorated") and method._already_decorated:  # pylint: disable=protected-access
            return method

        @wraps(method)
        def wrapped(*args, **kwargs):
            cls._steps_start()
            caught_exception = None
            result = None
            try:
                result = method(*args, **kwargs)
            except Exception as exc:
                caught_exception = exc
            finally:
                cls._check_exceptions_occured(caught_exception)
                if check_steps_end:
                    cls._check_steps_end()
            gc.collect()
            return result

        wrapped._already_decorated = True  # pylint: disable=protected-access
        return wrapped
