# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from moler.events.textualevent import TextualEvent
import re
import time


class LineEvent(TextualEvent):
    def __init__(self, connection=None, till_occurs_times=-1):
        super(LineEvent, self).__init__(connection=connection, till_occurs_times=till_occurs_times)
        self.process_full_lines_only = False

    def on_new_line(self, line, is_full_line):
        if is_full_line or not self.process_full_lines_only:
            for pattern in self.detect_patterns:
                if re.search(pattern, line):
                    current_ret = dict()
                    current_ret["line"] = line
                    current_ret["time"] = time.time()
                    self.event_occurred(event_data=current_ret)
                    return
