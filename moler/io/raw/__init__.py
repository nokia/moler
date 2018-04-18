# -*- coding: utf-8 -*-
"""
External-IO connections based on raw libraries like: sockets, subprocess, ...

The only 3 requirements for these connections is:
(1) store Moler's connection inside self.moler_connection attribute
(2) plugin into Moler's connection the way IO outputs data to external world:

    self.moler_connection.how2send = self.send

(3) forward IO received data into self.moler_connection.data_received(data)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import threading


class TillDoneThread(threading.Thread):
    def __init__(self, done_event, target=None, name=None, kwargs=None):
        super(TillDoneThread, self).__init__(target=target, name=name,
                                             kwargs=kwargs)
        self.done_event = done_event

    def join(self, timeout=None):
        """
        Wait until the thread terminates.
        Set event indicating "I'm done" before awaiting.
        """
        self.done_event.set()
        super(TillDoneThread, self).join(timeout=timeout)
