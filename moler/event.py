# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import re

from moler.connection_observer import ConnectionObserver
from moler.exceptions import NoDetectPatternProvided, MolerException
from moler.exceptions import ResultAlreadySet
from moler.helpers import instance_id


class Event(ConnectionObserver):

    def __init__(self, connection=None, till_occurs_times=-1, runner=None):
        super(Event, self).__init__(connection=connection, runner=runner)
        self.detect_pattern = ''
        self.detect_patterns = []
        self.callback = None
        self.callback_params = dict()
        self._occurred = []
        self.till_occurs_times = till_occurs_times
        self.event_name = Event.observer_name

    def __str__(self):
        detect_pattern = self.detect_pattern if not (self.detect_pattern is None) else ', '.join(self.detect_patterns)
        return '{}("{}", id:{})'.format(self.__class__.__name__, detect_pattern, instance_id(self))

    def start(self, timeout=None, *args, **kwargs):
        """Start background execution of command."""
        if self.detect_pattern and not self.detect_patterns:
            self.detect_patterns = [self.detect_pattern]
        self.detect_patterns = self.compile_patterns(self.detect_patterns)
        self._validate_start(*args, **kwargs)
        ret = super(Event, self).start(timeout, *args, **kwargs)
        self._is_running = True

        return ret

    def _validate_start(self, *args, **kwargs):
        # check base class invariants first
        super(Event, self)._validate_start(*args, **kwargs)
        # then what is needed for command
        if not self.detect_pattern and not self.detect_patterns:
            # no chance to start CMD
            raise NoDetectPatternProvided(self)

    def add_event_occurred_callback(self, callback):
        if not self.callback:
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

    def compile_patterns(self, patterns):
        compiled_patterns = []
        for pattern in patterns:
            if not hasattr(pattern, "match"):  # Not compiled regexp
                pattern = re.compile(pattern)
            compiled_patterns.append(pattern)
        return compiled_patterns

    def get_long_desc(self):
        return "Event '{}.{}':'{}'".format(self.__class__.__module__, self.__class__.__name__, self.detect_patterns)

    def get_short_desc(self):
        return "Event '{}.{}': '{}'".format(self.__class__.__module__, self.__class__.__name__, self.detect_patterns)
