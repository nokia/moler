# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import logging
import re
import time

from moler.event import Event


class Wait4prompt(Event):
    def __init__(self, connection, prompt=None, end_on_caught=True):
        super(Wait4prompt, self).__init__(connection=connection)
        self.connection = connection
        self.detect_pattern = prompt
        self.logger = logging.getLogger('moler.{}'.format(self))
        self.end_on_caught = end_on_caught

    def data_received(self, data):
        if not self.done():
            self._process_data(data=data, detect_pattern=self.detect_pattern)

    def _process_data(self, data, detect_pattern):
        if re.search(detect_pattern, data):
            self.notify()
            when_detected = time.time()
            self.logger.debug("Caught '{}' on Device '{}'!".format(detect_pattern, self.connection))

            if self.end_on_caught:
                self.set_result(result=when_detected)
