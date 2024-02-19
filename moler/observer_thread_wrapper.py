# -*- coding: utf-8 -*-

"""Wrapper for observer registered in ThreadedMolerConnection (old name: ObservableConnection)."""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020-2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import logging
import traceback
import threading
import queue
from moler.util import tracked_thread
from moler.config.loggers import TRACE
from moler.exceptions import CommandFailure, MolerException
from threading import Thread


class ObserverThreadWrapper:
    """Wrapper for observer registered in ThreadedMolerConnection (old name: ObservableConnection)."""

    _th_nr = 1

    def __init__(self, observer, observer_self, logger):
        """
        Construct wrapper for observer.

        :param observer: observer to wrap.
        :param observer_self: self for observer if observer is method from object or None if observer is a function.
        :param logger: logger to log.
        """
        self._observer = observer
        self._observer_self = observer_self
        self._queue = queue.Queue()
        self._request_end = threading.Event()
        self._timeout_for_get_from_queue = 1
        self.logger = logger
        self._t = Thread(target=self._loop_for_observer, name=f"ObserverThreadWrapper-{ObserverThreadWrapper._th_nr}-{observer_self}")
        ObserverThreadWrapper._th_nr += 1
        self._t.daemon = True
        self._t.start()

    def feed(self, data, recv_time):
        """
        Put data here.

        :param data: data to put.
        :param recv_time: time when data is received/read from connection.
        :return: None
        """
        self._queue.put((data, recv_time))

    def request_stop(self):
        """
        Call if you want to stop feed observer.

        :return: None
        """
        self._request_end.set()
        # self._t.join()  # only for debugging to have less active threads.
        if self._t:
            self._t = None

    @tracked_thread.log_exit_exception
    def _loop_for_observer(self):
        """
        Loop to pass data (put by method feed) to observer.

        :return: None
        """
        logging.getLogger("moler_threads").debug(f"ENTER {self._observer}")
        heartbeat = tracked_thread.report_alive()
        while not self._request_end.is_set():
            if next(heartbeat):
                logging.getLogger("moler_threads").debug("ALIVE")
            try:
                data, timestamp = self._queue.get(True, self._timeout_for_get_from_queue)
                try:
                    self.logger.log(level=TRACE, msg=f'notifying {self._observer}({repr(data)})')
                except ReferenceError:
                    self._request_end.set()  # self._observer is no more valid.
                try:
                    if self._observer_self:
                        self._observer(self._observer_self, data, timestamp)
                    else:
                        self._observer(data, timestamp)
                except ReferenceError:
                    self._request_end.set()  # self._observer is no more valid.
                except Exception as ex:
                    self._handle_unexpected_error_from_observer(exception=ex, data=data, timestamp=timestamp)
            except queue.Empty:
                pass  # No incoming data within self._timeout_for_get_from_queue
        self._observer = None
        self._observer_self = None
        logging.getLogger("moler_threads").debug("EXIT")

    # pylint: disable-next=unused-argument
    def _handle_unexpected_error_from_observer(self, exception, data, timestamp):
        self.logger.exception(f'Exception inside: {self._observer}({repr(data)}) at {timestamp}')


class ObserverThreadWrapperForConnectionObserver(ObserverThreadWrapper):

    def _handle_unexpected_error_from_observer(self, exception, data, timestamp):

        stack_msg = traceback.format_exc()
        self.logger.warning(f"Unhandled exception from '{self._observer_self}' caught by ObserverThreadWrapperForConnectionObserver"
                            f" (Runner normally). '{exception}' : '{repr(exception)}' \nStack:\n{stack_msg}.")
        ex_msg = f"Unexpected exception from {self._observer_self} caught by runner when processing data >>{data}<< at '{timestamp}':" \
                 f" >>>{exception}<<< -> repr: >>>{repr(exception)}<<<\n{stack_msg}"
        if self._observer_self.is_command():
            ex = CommandFailure(command=self._observer_self, message=ex_msg)
        else:
            ex = MolerException(ex_msg)
        self._observer_self.set_exception(exception=ex)
