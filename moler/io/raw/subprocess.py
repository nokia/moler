# -*- coding: utf-8 -*-
"""External-IO connections based on pyhon subprocess module."""

__author__ = 'Michal Plichta'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.plichta@nokia.com'


class Subprocess(object):
    def __init__(self):
        super(Subprocess, self).__init__()

    def start(self):
        pass

    def stop(self):
        pass

    def send(self, data):
        pass

    def receive(self, timeout=30):
        pass

    def data_received(self, data, recv_time):
        pass

    def read_subprocess_output(self):
        pass


class ThreadedSubprocess(Subprocess):
    def __init__(self):
        super(ThreadedSubprocess, self).__init__()

    def open(self):
        pass

    def close(self):
        pass

    def pull_data(self, pulling_done):
        pass
