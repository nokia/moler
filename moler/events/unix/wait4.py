# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import logging
import re
import time

from moler.event import Event


class Wait4(Event):
    def __init__(self, connection, detect_pattern=None, detect_patterns=None, callback=None, callback_params=None,
                 end_on_caught=True):
        super(Wait4, self).__init__(connection=connection)
        self.connection = connection
        self.detect_pattern = detect_pattern
        self.detect_patterns = detect_patterns
        self.logger = logging.getLogger('moler.{}'.format(self))
        self.end_on_caught = end_on_caught
        self.callback = callback
        self.callback_params = callback_params

    def data_received(self, data):
        if not self.done():
            if not (self.detect_pattern is None):
                self._process_data(data=data, detect_pattern=self.detect_pattern)
            elif self.detect_patterns:
                for detect_pattern in self.detect_patterns:
                    self._process_data(data=data, detect_pattern=detect_pattern)

    def _process_data(self, data, detect_pattern):
        if re.search(detect_pattern, data):
            when_detected = time.time()
            self.logger.debug("Caught '{}' on Device '{}'!".format(detect_pattern, self.connection))
            print("Caught '{}' on Device '{}'!".format(detect_pattern, self.connection))

            if self.end_on_caught:
                self.set_result(result=when_detected)
            if self.callback:
                self.callback(self, **self.callback_params)
