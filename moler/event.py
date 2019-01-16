# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'
import functools

from moler.connection_observer import ConnectionObserver
from moler.exceptions import MolerException
from moler.exceptions import ResultAlreadySet
from moler.helpers import instance_id


class Event(ConnectionObserver):

    def __init__(self, connection=None, till_occurs_times=-1, runner=None):
        super(Event, self).__init__(connection=connection, runner=runner)
        self.callback = None
        self.callback_params = dict()
        self._occurred = []
        self.till_occurs_times = till_occurs_times
        self.event_name = Event.observer_name

    def __str__(self):
        return '{}(id:{})'.format(self.__class__.__name__, instance_id(self))

    def start(self, timeout=None, *args, **kwargs):
        """Start background execution of command."""
        self._validate_start(*args, **kwargs)
        ret = super(Event, self).start(timeout, *args, **kwargs)
        self._is_running = True

        return ret

    def add_event_occurred_callback(self, callback, callback_params):
        if not self.callback:
            callback = functools.partial(callback, **callback_params)
            self.callback = callback
        else:
            raise MolerException("Cannot assign already assigned 'self.callback'.")

    def remove_event_occurred_callback(self):
        self.callback = None

    def notify(self):
        if self.callback:
            self.callback()

    def event_occurred(self, event_data):
        """Should be used to set final result"""
        if self.done():
            raise ResultAlreadySet(self)
        if self._occurred is None:
            self._occurred = []
        self._occurred.append(event_data)
        if self.till_occurs_times > 0:
            if len(self._occurred) >= self.till_occurs_times:
                self.set_result(self._occurred)
        self.notify()

    def get_long_desc(self):
        return "Event '{}.{}'".format(self.__class__.__module__, self.__class__.__name__)

    def get_short_desc(self):
        return "Event '{}.{}'".format(self.__class__.__module__, self.__class__.__name__)
