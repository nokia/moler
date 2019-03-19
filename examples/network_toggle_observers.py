# -*- coding: utf-8 -*-
"""
network_toggle_observers.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Example of connection observers catching
"network is down"/"network is up" events.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import logging
import time

from moler.connection_observer import ConnectionObserver


class NetworkToggleDetector(ConnectionObserver):
    def __init__(self, net_ip, detect_pattern, detected_status,
                 connection=None, runner=None):
        super(NetworkToggleDetector, self).__init__(connection=connection,
                                                    runner=runner)
        self.net_ip = net_ip
        self.detect_pattern = detect_pattern
        self.detected_status = detected_status
        self.logger = logging.getLogger('moler.{}'.format(self))

    def data_received(self, data):
        """Awaiting ping output change"""
        if not self.done():
            if self.detect_pattern in data:
                when_detected = time.time()
                self.logger.debug("Network {} {}!".format(self.net_ip,
                                                          self.detected_status))
                self.set_result(result=when_detected)


class NetworkDownDetector(NetworkToggleDetector):
    """
    Awaiting change like:
    64 bytes from 10.0.2.15: icmp_req=3 ttl=64 time=0.045 ms
    ping: sendmsg: Network is unreachable
    """
    def __init__(self, net_ip, connection=None, runner=None):
        detect_pattern = "Network is unreachable"
        detected_status = "is down"
        super(NetworkDownDetector, self).__init__(net_ip,
                                                  detect_pattern,
                                                  detected_status,
                                                  connection=connection,
                                                  runner=runner)


class NetworkUpDetector(NetworkToggleDetector):
    """
    Awaiting change like:
    ping: sendmsg: Network is unreachable
    64 bytes from 10.0.2.15: icmp_req=7 ttl=64 time=0.123 ms
    """
    def __init__(self, net_ip, connection=None, runner=None):
        detect_pattern = "bytes from {}".format(net_ip)
        detected_status = "is up"
        super(NetworkUpDetector, self).__init__(net_ip,
                                                detect_pattern,
                                                detected_status,
                                                connection=connection,
                                                runner=runner)
