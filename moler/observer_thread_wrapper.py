# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from threading import Thread
from moler.config.loggers import TRACE

try:
    import queue
except ImportError:
    import Queue as queue  # For python 2


class ObserverThreadWrapper(object):
    """
    Wrapper for observer registered in ThreadedMolerConnection (old name: ObservableConnection).
    """

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
        self._request_end = False
        self._timeout_for_get_from_queue = 1
        self.logger = logger
        t = Thread(target=self._loop_for_observer)
        t.setDaemon(True)
        t.start()

    def feed(self, data, recv_time):
        """
        Put data here.

        :param data: data to put.
        :return: None
        """
        self._queue.put((data, recv_time))

    def request_stop(self):
        """
        Call if you want to stop feed observer.
        :return: None
        """
        self._request_end = True

    def _loop_for_observer(self):
        """
        Loop to pass data (put by method feed) to observer.
        :return: None
        """
        while self._request_end is False:
            try:
                data, timestamp = self._queue.get(True, self._timeout_for_get_from_queue)
                try:
                    self.logger.log(level=TRACE, msg=r'notifying {}({!r})'.format(self._observer, repr(data)))
                except ReferenceError:
                    self._request_end = True  # self._observer is no more valid.
                try:
                    if self._observer_self:
                        self._observer(self._observer_self, data, timestamp)
                    else:
                        self._observer(data, timestamp)
                except ReferenceError:
                    self._request_end = True  # self._observer is no more valid.
                except Exception:
                    self.logger.exception(msg=r'Exception inside: {}({!r})'.format(self._observer, repr(data)))
            except queue.Empty:
                pass  # No incoming data within self._timeout_for_get_from_queue
        self._observer = None
        self._observer_self = None
