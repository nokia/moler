# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

from abc import ABCMeta

from six import add_metaclass
from threading import Lock
from copy import copy

from moler.connection_observer import ConnectionObserver
from moler.exceptions import NoDetectPatternProvided
from moler.helpers import instance_id


@add_metaclass(ABCMeta)
class Event(ConnectionObserver):
    def __init__(self, connection=None):
        super(Event, self).__init__(connection=connection)
        self.detect_pattern = ''
        self.detect_patterns = []
        self.subscribers_lock = Lock()
        self.subscribers = list()

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

    def notify(self):
        with self.subscribers_lock:
            copied_subscribers = copy(self.subscribers)
            for subscriber in copied_subscribers:
                subscriber[0](self, **subscriber[1])

    def subscribe(self, callback, callback_params={}):
        with self.subscribers_lock:
            if (callback, callback_params) not in self.subscribers:
                self.subscribers.append((callback, callback_params))

    def unsubscribe(self, ):
        self.subscribers = list()
