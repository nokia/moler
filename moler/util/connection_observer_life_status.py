# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020 Nokia'
__email__ = 'marcin.usielski@nokia.com'


class ConnectionObserverLifeStatus(object):

    def __init__(self):
        """
        Creates instance of ConnectionObserverLifeStatus class.
        """
        self.inactivity_timeout = 0.0  # If positive value and no data are sent by connection in this time then method
        #                                on_inactivity will be called.
        self.last_feed_time = None  # Time of last called data_received or on_inactivity.
        self.start_time = 0.0  # means epoch: 1970-01-01 00:00:00
        self.in_terminating = False  # Set True if ConnectionObserver object is just after __timeout but it can do
        #                              something during terminating_timeout. False if the ConnectionObserver object runs
        #                              during normal timeout. For Runners only!
        self.was_on_timeout_called = False  # Set True if method on_timeout was called. False otherwise. For Runners
        #                                     only!

