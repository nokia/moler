# -*- coding: utf-8 -*-
__author__ = "Michal Ernst, Marcin Usielski"
__copyright__ = "Copyright (C) 2019-2024, Nokia"
__email__ = "michal.ernst@nokia.com, marcin.usielski@nokia.com"

import datetime
import re
from operator import attrgetter

from moler.events.unix.genericunix_textualevent import GenericUnixTextualEvent
from moler.exceptions import ParsingDone
from moler.helpers import copy_dict


class Wait4prompts(GenericUnixTextualEvent):
    def __init__(self, connection, prompts, till_occurs_times=-1, runner=None):
        """
        Event for waiting for prompt
        :param connection: moler connection to device, terminal when command is executed
        :param prompts: prompts->state regex dict. Key is regex, value is state.
        :param till_occurs_times: number of event occurrence
        :param runner: Runner to run event
        """
        super(Wait4prompts, self).__init__(
            connection=connection, runner=runner, till_occurs_times=till_occurs_times
        )
        self.compiled_prompts_regex = (
            None  # Dict, key is a compiled regex, value is state name
        )
        self._prompts_list = None  # List of compiled regexps
        self._set_prompts(prompts=prompts)

        self.process_full_lines_only = False
        self.check_against_all_prompts = False
        self._ret_list_matched = []

        # Change default order and behavior after matching the prompt
        self._reverse_order = True
        self._break_processing_when_found = True

    def on_new_line(self, line, is_full_line):
        try:
            self._parse_prompts(line)
        except ParsingDone:
            pass

    def change_prompts(self, prompts):
        self.pause()
        self._set_prompts(prompts=prompts)
        self.resume()
        self.logger.info(f"Changed prompts into '{prompts}'.")

    def _set_prompts(self, prompts):
        self.compiled_prompts_regex = self._compile_prompts_patterns(prompts=prompts)
        self._prompts_list = sorted(
            self.compiled_prompts_regex.keys(), key=attrgetter("pattern")
        )

    def _parse_prompts(self, line):
        current_ret = None
        for prompt_regex in self._prompts_list:
            if self._regex_helper.search_compiled(prompt_regex, line):
                current_ret = {
                    "line": line,
                    "prompt_regex": prompt_regex.pattern,
                    "matched": self._regex_helper.group(0),
                    "state": self.compiled_prompts_regex[prompt_regex],
                    "time": datetime.datetime.now(),
                }
                if self.check_against_all_prompts:
                    self._ret_list_matched.append(copy_dict(current_ret))
                else:
                    break
        if current_ret:
            if self.check_against_all_prompts:
                current_ret["list_matched"] = self._ret_list_matched
                self._ret_list_matched = []
            self.event_occurred(event_data=current_ret)
            raise ParsingDone()

    def _compile_prompts_patterns(self, prompts):
        compiled_patterns = {}
        for pattern in prompts.keys():
            if not hasattr(pattern, "match"):  # Not compiled regexp
                compiled_pattern = re.compile(pattern)
            else:
                compiled_pattern = pattern
            compiled_patterns[compiled_pattern] = prompts[pattern]
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

EVENT_KWARGS = {"prompts": {r"host:.*#": "UNIX_LOCAL"}, "till_occurs_times": 1}

EVENT_RESULT = [
    {
        "line": "host:~ #",
        "matched": "host:~ #",
        "prompt_regex": "host:.*#",
        "state": "UNIX_LOCAL",
        "time": datetime.datetime(2019, 8, 22, 12, 42, 38, 278418),
    }
]

EVENT_OUTPUT_compiled = """
user@host01:~> TERM=xterm-mono telnet -4 host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ #"""

EVENT_KWARGS_compiled = {
    "prompts": {re.compile(r"host:.*#"): "UNIX_LOCAL"},
    "till_occurs_times": 1,
}

EVENT_RESULT_compiled = [
    {
        "line": "host:~ #",
        "matched": "host:~ #",
        "prompt_regex": "host:.*#",
        "state": "UNIX_LOCAL",
        "time": datetime.datetime(2019, 8, 22, 12, 42, 38, 278418),
    }
]
