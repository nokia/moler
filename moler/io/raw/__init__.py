# -*- coding: utf-8 -*-
"""
External-IO connections based on raw libraries like: sockets, subprocess, ...

The only 3 requirements for these connections is:
(1) store Moler's connection inside self.moler_connection attribute
(2) plugin into Moler's connection the way IO outputs data to external world:

    self.moler_connection.how2send = self.send

(3) forward IO received data into self.moler_connection.data_received(data)
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2021, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'

import threading


class TillDoneThread(threading.Thread):

    _tdh_nr = 1

    def __init__(self, done_event, target=None, name=None, kwargs=None):
        if name is None:
            name = "TillDoneThread-{}".format(TillDoneThread._tdh_nr)
            TillDoneThread._tdh_nr += 1
        super(TillDoneThread, self).__init__(target=target, name=name,
                                             kwargs=kwargs)
        self.done_event = done_event
        self.daemon = True

    def join(self, timeout=None):
        """
        Wait until the thread terminates.
        Set event indicating "I'm done" before awaiting.
        """
        self.done_event.set()
        super(TillDoneThread, self).join(timeout=timeout)
