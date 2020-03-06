# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import functools
import abc
import six
import logging
from moler.connection_observer import ConnectionObserver
from moler.exceptions import MolerException
from moler.exceptions import ResultAlreadySet
from moler.helpers import instance_id


@six.add_metaclass(abc.ABCMeta)
class Event(ConnectionObserver):

    def __init__(self, connection=None, till_occurs_times=-1, runner=None):
        """

        :param connection: connection to observe.
        :param till_occurs_times: If -1 then infinite. If positive value match the number of times.
        :param runner: runner to run event.
        """
        super(Event, self).__init__(connection=connection, runner=runner)
        # By default events are infinite (100 years :-) so, they won't timeout since they are
        # mainly designed to catch something inside event_occurred(), notify interested parties and keep going.
        self.timeout = 60 * 60 * 24 * 356 * 100  # [sec]
        self.callback = None
        self.callback_params = dict()
        self._occurred = None
        self.till_occurs_times = till_occurs_times
        self._log_every_occurrence = True
        self.event_name = Event.observer_name

    def __str__(self):
        """
        Returns description of event object.

        :return: String representation of event.
        """
        return '{}(id:{})'.format(self.__class__.__name__, instance_id(self))

    def start(self, timeout=None, *args, **kwargs):
        """Start background execution of command."""
        self._validate_start(*args, **kwargs)
        ret = super(Event, self).start(timeout, *args, **kwargs)
        self.life_status._is_running = True
        return ret

    def add_event_occurred_callback(self, callback, callback_params=None):
        if not self.callback:
            if callback_params is None:
                callback_params = dict()
            partial_callback = functools.partial(callback, **callback_params)
            self.callback = partial_callback
        else:
            raise MolerException("Cannot assign a callback '{}' to event '{}' when another callback '{}' is already "
                                 "assigned".format(callback, self, self.callback))

    def enable_log_occurrence(self):
        """
        Enables to log every occurrence of the event.

        :return: None
        """
        self._log_every_occurrence = True

    def disable_log_occurrence(self):
        """
        Disables to log every occurrence of the event.

        :return: None
        """
        self._log_every_occurrence = False

    def remove_event_occurred_callback(self):
        """
        Removes callback from the event.

        :return: None
        """
        self.callback = None

    def notify(self):
        """
        Notifies (call callback).

        :return: None
        """
        self._log_occurred()
        if self.callback:
            self.callback()

    def event_occurred(self, event_data):
        """
        Sets event_data as new item of occurrence ret.
        :param event_data: data to set as value of occurrence.
        :return: None
        """
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

    def _get_module_class(self):
        return "{}.{}".format(self.__class__.__module__, self)

    def get_long_desc(self):
        """
        Returns string with description of event.

        :return: String with description.
        """
        return "Event '{}'".format(self._get_module_class())

    def get_short_desc(self):
        """
        Returns string with description of event.

        :return: String with description.
        """
        return self.get_long_desc()

    def get_last_occurrence(self):
        """
        Returns ret value from last occurrence.

        :return: ret value form last occurrence or None if there is no occurrence.
        """
        if self._occurred:
            return self._occurred[-1]
        else:
            return None

    def _log_occurred(self):
        """
        Logs info about notify when callback is not defined.

        :return: None
        """
        msg = "Notify for event:  '{}.{}'".format(self.__class__.__module__, self)
        if self._log_every_occurrence:
            self._log(lvl=logging.INFO, msg=msg)
        if self.callback:
            msg = "{} with callback '{}'.".format(msg, self.callback)
        else:
            msg = "{} without callback.".format(msg)
        self._log(lvl=logging.DEBUG, msg=msg)

    @abc.abstractmethod
    def pause(self):
        """
        Pauses the event. Do not process till resume.

        :return: None.
        """

    @abc.abstractmethod
    def resume(self):
        """
        Resumes processing output from connection by the event.

        :return: None.
        """
