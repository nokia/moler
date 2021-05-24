# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020-2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from threading import Thread
from moler.config.loggers import TRACE
import time

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

        self._tick_for_runner = 0.01
        self.logger = logger
        self._connections_obsevers = list()
        self._to_remove_connection_observers = list()
        self._queue_for_connection_observers = queue.Queue()

        t = Thread(target=self._loop_for_observer)
        t.setDaemon(True)
        t.start()

        t = Thread(target=self._loop_for_runner)  # One thread for all commands and events.
        t.setDaemon(True)
        t.start()

    def add_connection_observer(self, connection_observer):
        if connection_observer not in self._connections_obsevers:
            self._connections_obsevers.append(connection_observer)

    def feed(self, data, recv_time):
        """
        Put data here.

        :param data: data to put.
        :return: None
        """
        data_to_put = (data, recv_time)
        self._queue.put(data_to_put)
        self._queue_for_connection_observers.put(data_to_put)

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

    def _loop_for_runner(self):
        while True:
            if not self._connections_obsevers:
                time.sleep(self._tick_for_runner)

            for connection_observer in self._connections_obsevers:
                try:
                    current_time = time.time()
                except Exception as ex:
                    self.logger.exception(msg=r'Exception from "{}" when running checking: "{}" "{!r}".'.format(
                        connection_observer, ex, repr(ex)
                    ))
            self._remove_unecessary_connection_observers()

    def _remove_unecessary_connection_observers(self):
        for connection_observer in self._connections_obsevers:
            if connection_observer.done():
                self._to_remove_connection_observers.append(connection_observer)
        if self._to_remove_connection_observers:
            for connection_observer in self._to_remove_connection_observers:
                self._connections_obsevers.remove(connection_observer)
            self._to_remove_connection_observers.clear()

    def _feed_connection_observer(self):
        try:
            data, timestamp = self._queue_for_connection_observers.get(True, self._tick_for_runner)
            try:
                self.logger.log(level=TRACE, msg=r'notifying {}({!r})'.format(self._observer, repr(data)))
            except ReferenceError:
                self._request_end = True  # self._observer is no more valid.
            try:
                    self._observer(self._observer_self, data, timestamp)
                else:
                    self._observer(data, timestamp)
            except ReferenceError:
                self._request_end = True  # self._observer is no more valid.
            except Exception:
                self.logger.exception(msg=r'Exception inside: {}({!r})'.format(self._observer, repr(data)))
        except queue.Empty:
            pass  # No incoming data within self._tick_for_runner

    def submit(self, connection_observer):
        """
        Submit connection observer to background execution.
        Returns Future that could be used to await for connection_observer done.
        """
        assert connection_observer.life_status.start_time > 0.0  # connection-observer lifetime should already been
        #self.logger.debug("go background: {!r} - {}".format(connection_observer, msg))
        self._connections_obsevers.append(connection_observer)
        self._start_command(connection_observer=connection_observer)

    def _start_command(self, connection_observer):
        if connection_observer.is_command():
            connection_observer.send_command()
