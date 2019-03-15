# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski, Tomasz Krol'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'marcin.usielski@nokia.com, tomasz.krol@nokia.com'

import datetime
import re

from moler.events.textualevent import TextualEvent
from moler.exceptions import NoDetectPatternProvided
from moler.helpers import instance_id, copy_list


class LineEvent(TextualEvent):
    def __init__(self, detect_patterns=list(), connection=None, till_occurs_times=-1, match='any'):
        super(LineEvent, self).__init__(connection=connection, till_occurs_times=till_occurs_times)
        self.detect_patterns = copy_list(detect_patterns)
        self.process_full_lines_only = False
        self.match = match
        self._prepare_parameters(match)

    def __str__(self):
        return '{}({}, id:{})'.format(self.__class__.__name__, self.detect_patterns, instance_id(self))

    def start(self, timeout=None, *args, **kwargs):
        """Start background execution of command."""

        self._validate_start(*args, **kwargs)
        ret = super(LineEvent, self).start(timeout, *args, **kwargs)
        self._is_running = True

        return ret

    def _validate_start(self, *args, **kwargs):
        # check base class invariants first
        super(LineEvent, self)._validate_start(*args, **kwargs)
        # then what is needed for command
        if not self.detect_patterns:
            # no chance to start CMD
            raise NoDetectPatternProvided(self)

    def on_new_line(self, line, is_full_line):
        if is_full_line or not self.process_full_lines_only:
            self._parse_line(line=line)

    def compile_patterns(self, patterns):
        compiled_patterns = []
        for pattern in patterns:
            if not hasattr(pattern, "match"):  # Not compiled regexp
                pattern = re.compile(pattern)
            compiled_patterns.append(pattern)
        return compiled_patterns

    def get_long_desc(self):
        return "Event {}.{}".format(self.__class__.__module__, str(self))

    def get_short_desc(self):
        return "Event {}.{}".format(self.__class__.__module__, str(self))

    def get_parser(self, match):
        parsers = {
            "any": self._catch_any,
            "all": self._catch_all,
            "sequence": self._catch_sequence,
        }
        if match in parsers:
            return parsers[match]

    def _prepare_parameters(self, match):
        self.parser = self.get_parser(match)
        self.compiled_patterns = self.compile_patterns(self.detect_patterns)

        if match in ['all', 'sequence']:
            self.finished_cycles = 0
            self.number_of_cycles = self.till_occurs_times
            self.till_occurs_times = len(self.detect_patterns) * self.till_occurs_times
            self.copy_compiled_patterns = copy_list(self.compiled_patterns)

    def _parse_line(self, line):
        self.parser(line=line)

    def _set_current_ret(self, line, match):
        current_ret = dict()
        current_ret["line"] = line
        current_ret["time"] = datetime.datetime.now()
        current_ret["groups"] = match.groups()
        current_ret["named_groups"] = match.groupdict()
        current_ret["matched"] = match.group(0)
        self.event_occurred(event_data=current_ret)

    def _catch_any(self, line):
        for pattern in self.compiled_patterns:
            match = re.search(pattern, line)
            if match:
                self._set_current_ret(line=line, match=match)
                return

    def _catch_all(self, line):
        for index, pattern in enumerate(self.copy_compiled_patterns):
            match = re.search(pattern, line)
            if match:
                del self.copy_compiled_patterns[index]
                self._prepare_parameters_when_single_cycle_finished()
                self._set_current_ret(line=line, match=match)
                return

    def _catch_sequence(self, line):
        if self.copy_compiled_patterns:
            pattern = self.copy_compiled_patterns[0]
            match = re.search(pattern, line)
            if match:
                del self.copy_compiled_patterns[0]
                self._prepare_parameters_when_single_cycle_finished()
                self._set_current_ret(line=line, match=match)

    def _prepare_new_cycle_parameters(self):
        self.finished_cycles += 1
        self.copy_compiled_patterns = copy_list(self.compiled_patterns)

    def _prepare_parameters_when_single_cycle_finished(self):
        if not len(self.copy_compiled_patterns):
            self._prepare_new_cycle_parameters()


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
    "detect_patterns": [r'host:.*#'],
    "till_occurs_times": 1
}

EVENT_RESULT_single_pattern = [
    {
        'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224929),
        "groups": (),
        "named_groups": {},
        "matched": "host:~ #",
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
    "detect_patterns": ['Last login', r'host:.*#'],
    "till_occurs_times": 2
}

EVENT_RESULT_patterns_list = [
    {
        'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224929),
        "groups": (),
        "named_groups": {},
        "matched": "Last login",
        'line': "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1"
    },
    {
        'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224929),
        "groups": (),
        "named_groups": {},
        "matched": "host:~ #",
        'line': "host:~ #"
    }
]
