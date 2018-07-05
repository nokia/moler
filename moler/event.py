# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

from moler.connection_observer import ConnectionObserver
from moler.exceptions import NoDetectPatternProvided
from moler.helpers import instance_id


class Event(ConnectionObserver):
    def __init__(self, connection=None):
        super(Event, self).__init__(connection=connection)
        self.detect_pattern = ''
        self.detect_patterns = []
        self.callback = None
        self.callback_params = dict()
        self.event_name = Event.observer_name

    def __str__(self):
        detect_pattern = self.detect_pattern if not (self.detect_pattern is None) else ', '.join(self.detect_patterns)
        return '{}("{}", id:{})'.format(self.__class__.__name__, detect_pattern, instance_id(self))

    def start(self, timeout=None, *args, **kwargs):
        """Start background execution of command."""
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

    def subscribe(self, callback, callback_params={}):
        self.callback = callback
        self.callback_params = callback_params

    def unsubscribe(self):
        if not (self.callback_params is None):
            self.callback = None
            self.callback_params = dict()

    def notify(self):
        self.callback(self, **self.callback_params)
