# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com, michal.ernst@nokia.com'

from moler.events.lineevent import LineEvent


class Wait4prompt(LineEvent):
    def __init__(self, connection, prompt=None, till_occurs_times=-1):
        super(Wait4prompt, self).__init__(connection=connection, till_occurs_times=till_occurs_times)
        self.connection = connection
        self.detect_pattern = prompt
