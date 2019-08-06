# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import functools
import abc
import six
from moler.connection_observer import ConnectionObserver
from moler.exceptions import MolerException
from moler.exceptions import ResultAlreadySet
from moler.helpers import instance_id


@six.add_metaclass(abc.ABCMeta)
class Event(ConnectionObserver):

    def __init__(self, connection=None, till_occurs_times=-1, runner=None):
        super(Event, self).__init__(connection=connection, runner=runner)
        # By default events are infinite (100 years :-) so, they won't timeout since they are
        # mainly designed to catch something inside event_occurred(), notify interested parties and keep going.
        self.timeout = 60 * 60 * 24 * 356 * 100  # [sec]
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
        self._log_occurred()
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
        return "Event '{}.{}'".format(self.__class__.__module__, self)

    def get_short_desc(self):
        return "Event '{}.{}'".format(self.__class__.__module__, self)

    def get_last_occurrence(self):
        if self._occurred:
            return self._occurred[-1]
        else:
            return None

    def _log_occurred(self):
        """
        Logs info about notify when callback is not define.

        :return: None
        """
        msg = "Notify for event:  '{}.{}'".format(self.__class__.__module__, self)
        if self.callback:
            msg = "{} with callback '{}'.".format(msg, self.callback)
        else:
            msg = "{} without callback.".format(msg)
        self.logger.info(msg=msg)
