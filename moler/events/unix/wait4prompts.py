# -*- coding: utf-8 -*-
__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'michal.ernst@nokia.com'
import datetime
import re

from moler.events.textualevent import TextualEvent
from moler.exceptions import ParsingDone


class Wait4prompts(TextualEvent):
    def __init__(self, connection, prompts, till_occurs_times=-1, runner=None):
        """
        Event for waiting for prompt
        :param connection: moler connection to device, terminal when command is executed
        :param prompt: prompt regex
        :param till_occurs_times: number of event occurrence
        :param runner: Runner to run event
        """
        super(Wait4prompts, self).__init__(connection=connection, runner=runner, till_occurs_times=till_occurs_times)
        self.compiled_prompts = self.compile_prompts_patterns(prompts)
        self.process_full_lines_only = False

    def on_new_line(self, line, is_full_line):
        try:
            self._parse_prompts(line)
        except ParsingDone:
            pass

    def _parse_prompts(self, line):
        for prompt in self.compiled_prompts.keys():
            if self._regex_helper.search_compiled(prompt, line):
                current_ret = {
                    'line': line,
                    'prompt': prompt.pattern,
                    'state': self.compiled_prompts[prompt],
                    'time': datetime.datetime.now()
                }
                self.event_occurred(event_data=current_ret)

                raise ParsingDone()

    def compile_prompts_patterns(self, patterns):
        compiled_patterns = dict()
        for pattern in patterns.keys():
            if not hasattr(pattern, "match"):  # Not compiled regexp
                compiled_pattern = re.compile(pattern)
            else:
                compiled_pattern = pattern
            compiled_patterns[compiled_pattern] = patterns[pattern]
        return compiled_patterns


EVENT_OUTPUT = """
user@host01:~> TERM=xterm-mono telnet -4 host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ #"""

EVENT_KWARGS = {
    "prompts": {r'host:.*#': "UNIX_LOCAL"},
    "till_occurs_times": 1
}

EVENT_RESULT = [
    {
        'line': "host:~ #",
        "prompt": "host:.*#",
        "state": "UNIX_LOCAL",
        'time': datetime.datetime(2019, 8, 22, 12, 42, 38, 278418)
    }
]
