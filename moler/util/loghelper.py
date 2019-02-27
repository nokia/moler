# -*- coding: utf-8 -*-
# Copyright (C) 2018 Nokia
"""
Utilities related to logging
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import os
import logging
import contextlib


def __dummy():
    pass


_srcfile = os.path.normcase(__dummy.__code__.co_filename)


def find_caller(levels_to_go_up=0):
    """
    Find the stack frame of the caller so that we can note the source
    file name, line number and function name.

    Based on findCaller() from logging module
    but allows to go higher back on stack

    :param levels_to_go_up: 0 - info about 'calling location' of caller of findCaller(); 1 - 'calling -1 location'
    :return:
    """
    f = logging.currentframe()
    # On some versions of IronPython, currentframe() returns None if
    # IronPython isn't run with -X:Frames.
    rv = "(unknown file)", 0, "(unknown function)", None
    while hasattr(f, "f_code"):
        co = f.f_code
        filename = os.path.normcase(co.co_filename)
        if filename == _srcfile:
            f = f.f_back
            continue
        for lv in range(levels_to_go_up):
            f = f.f_back
            if hasattr(f, "f_code"):
                co = f.f_code
            else:
                break

        rv = (co.co_filename, f.f_lineno, co.co_name)
        break
    return rv


def error_into_logger(logger, msg, extra=None, levels_to_go_up=0):
    log_into_logger(logger, logging.ERROR, msg, extra=extra, levels_to_go_up=levels_to_go_up)


def warning_into_logger(logger, msg, extra=None, levels_to_go_up=0):
    log_into_logger(logger, logging.WARNING, msg, extra=extra, levels_to_go_up=levels_to_go_up)


def info_into_logger(logger, msg, extra=None, levels_to_go_up=0):
    log_into_logger(logger, logging.INFO, msg, extra=extra, levels_to_go_up=levels_to_go_up)


def debug_into_logger(logger, msg, extra=None, levels_to_go_up=0):
    log_into_logger(logger, logging.DEBUG, msg, extra=extra, levels_to_go_up=levels_to_go_up)


def log_into_logger(logger, level, msg, extra=None, levels_to_go_up=0):
    """
    Log into specific logger

    No support for logging exceptions

    :param logger: logger to send log record into
    :param level: logging level
    :param msg: message to be logged
    :param levels_to_go_up: 0 - info about function using log_into_logger(), 1 - caller of that function, ...
    :return: None
    """
    if logger.isEnabledFor(level):
        try:
            fn, lno, func = find_caller(levels_to_go_up)
        except ValueError:  # pragma: no cover
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        record = logger.makeRecord(logger.name, level, fn, lno, msg, [], None, func, extra)
        logger.handle(record)


@contextlib.contextmanager
def disabled_logging(from_level_and_below=logging.INFO):
    logging.disable(from_level_and_below)
    yield
    logging.disable(logging.NOTSET)
