# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import datetime
import re

from moler.events.textualevent import TextualEvent
from moler.exceptions import NoDetectPatternProvided
from moler.helpers import instance_id, copy_list


class LineEvent(TextualEvent):
    def __init__(self, detect_pattern=None, detect_patterns=list(), connection=None, till_occurs_times=-1):
        super(LineEvent, self).__init__(connection=connection, till_occurs_times=till_occurs_times)
        self.detect_pattern = detect_pattern
        self.detect_patterns = copy_list(detect_patterns)
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
                    current_ret["time"] = datetime.datetime.now()
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


EVENT_OUTPUT_single_pattern = """
user@host01:~> TERM=xterm-mono telnet -4 host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ #"""

EVENT_KWARGS_single_pattern = {
    "detect_pattern": r'host:.*#',
    "till_occurs_times": 1
}

EVENT_RESULT_single_pattern = [
    {
        'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224929),
        'line': "host:~ #"
    }
]

EVENT_OUTPUT_patterns_list = """
user@host01:~> TERM=xterm-mono telnet -4 host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ #"""

EVENT_KWARGS_patterns_list = {
    "detect_pattern": r'host:.*#',
    "till_occurs_times": 1
}

EVENT_RESULT_patterns_list = [
    {
        'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224929),
        'line': "host:~ #"
    }
]
