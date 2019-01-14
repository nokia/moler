# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
import time

from moler.events.textualevent import TextualEvent
from moler.exceptions import NoDetectPatternProvided
from moler.helpers import instance_id


class LineEvent(TextualEvent):
    def __init__(self, connection=None, till_occurs_times=-1):
        super(LineEvent, self).__init__(connection=connection, till_occurs_times=till_occurs_times)
        self.detect_pattern = ''
        self.detect_patterns = []
        self.process_full_lines_only = False

    def __str__(self):
        detect_pattern = self.detect_pattern if not (self.detect_pattern is None) else ', '.join(self.detect_patterns)
        return '{}("{}", id:{})'.format(self.__class__.__name__, detect_pattern, instance_id(self))

    def start(self, timeout=None, *args, **kwargs):
        """Start background execution of command."""
        if self.detect_pattern and not self.detect_patterns:
            self.detect_patterns = [self.detect_pattern]
        self.detect_patterns = self.compile_patterns(self.detect_patterns)
        self._validate_start(*args, **kwargs)
        ret = super(LineEvent, self).start(timeout, *args, **kwargs)
        self._is_running = True

        return ret

    def _validate_start(self, *args, **kwargs):
        # check base class invariants first
        super(LineEvent, self)._validate_start(*args, **kwargs)
        # then what is needed for command
        if not self.detect_pattern and not self.detect_patterns:
            # no chance to start CMD
            raise NoDetectPatternProvided(self)

    def on_new_line(self, line, is_full_line):
        if is_full_line or not self.process_full_lines_only:
            for pattern in self.detect_patterns:
                if re.search(pattern, line):
                    current_ret = dict()
                    current_ret["line"] = line
                    current_ret["time"] = time.time()
                    self.event_occurred(event_data=current_ret)
                    return

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
