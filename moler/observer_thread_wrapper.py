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
    def __init__(self, observer, observer_self, logger):
        self._observer = observer
        self._observer_self = observer_self
        self._queue = queue.Queue()
        self._request_end = False
        self._timeout_for_get_from_queue = 1
        self.logger = logger
        t = Thread(target=self._loop_for_observer)
        t.setDaemon(True)
        t.start()

    def feed(self, data):
        self._queue.put(data)

    def request_stop(self):
        self._request_end = True

    def _loop_for_observer(self):
        while self._request_end is False:
            try:
                data = self._queue.get(True, self._timeout_for_get_from_queue)
                try:
                    self.logger.log(level=TRACE, msg=r'notifying {}({!r})'.format(self._observer, repr(data)))
                except ReferenceError:
                    self._request_end = True  # self._observer is no more valid.
                try:
                    if self._observer_self:
                        self._observer(self._observer_self, data)
                    else:
                        self._observer(data)
                except ReferenceError:
                    self._request_end = True  # self._observer is no more valid.
                except Exception:
                    self.logger.exception(msg=r'Exception inside: {}({!r})'.format(self._observer, repr(data)))
            except queue.Empty:
                pass  # No incoming data within self._timeout_for_get_from_queue
        self._observer = None
        self._observer_self = None
