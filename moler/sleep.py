# -*- coding: utf-8 -*-
"""
Package Open Source functionality of Moler.
"""
import time

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'


class Sleep(object):
    """
    Module adding into tests sleep functionality between different type of parallelism
    """
    @staticmethod
    def sleep(seconds):
        """
        :param seconds: Time to sleep (in seconds)
        :return:
        """
        time.sleep(seconds)
