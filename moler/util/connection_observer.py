# -*- coding: utf-8 -*-
"""
Utilities related to connection-observers
"""
__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2025 Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'

import logging
import threading
import sys
import traceback


def inside_main_thread():
    in_main_thread = threading.current_thread() is threading.main_thread()
    return in_main_thread


class exception_stored_if_not_main_thread:
    """
    Context manager storing exception inside connection-observer for non-main threads
    """
    def __init__(self, connection_observer, logger=None):
        self.connection_observer = connection_observer
        self.logger = logger if logger else logging.getLogger('moler')

    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            if inside_main_thread():
                return False  # will reraise exception
            else:
                mg = traceback.format_list(traceback.extract_stack())
                stack_msg = f"{''.join(mg)}\n  {exc_val.__class__} {exc_val} traceback:".join(
                    traceback.format_tb(exc_val.__traceback__)
                )
                err_msg = f"NOT MainThread: {self.connection_observer} raised {exc_val!r} {stack_msg}"
                self.logger.debug(err_msg)
                sys.stderr.write(f"{err_msg}\n")
                self.connection_observer.set_exception(exc_val)

                return True  # means: exception already handled
        return True
