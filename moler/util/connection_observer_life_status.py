# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020-2024 Nokia'
__email__ = 'marcin.usielski@nokia.com'


from typing import Optional


class ConnectionObserverLifeStatus:

    def __init__(self):
        """
        Creates instance of ConnectionObserverLifeStatus class.
        """
        self.inactivity_timeout: float = 0.0  # If positive value and no data are sent by connection in this time then method
        #                                on_inactivity will be called.
        self.last_feed_time: Optional[float] = None  # Time of last called data_received or on_inactivity.
        self.start_time: float = 0.0  # means epoch: 1970-01-01 00:00:00
        self.in_terminating: bool = False  # Set True if ConnectionObserver object is just after __timeout but it can do
        #                              something during terminating_timeout. False if the ConnectionObserver object runs
        #                              during normal timeout. For Runners only!
        self.was_on_timeout_called: bool = False  # Set True if method on_timeout was called. False otherwise. For Runners
        #                                           only!
        self._is_running: bool = False
        self.terminating_timeout: float = 0.0  # value for terminating connection_observer when it timeouts. Set positive value
        #                                        for command if they can do anything if timeout. Set 0 for observer or command
        #                                        if it cannot do anything if timeout.
        self.timeout: Optional[float] = 20.0  # default
        self.is_done: bool = False
        self.is_cancelled: bool = False
