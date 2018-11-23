# -*- coding: utf-8 -*-
"""
Package Open Source functionality of Moler.
"""
import time
from moler.util.moler_test import MolerTest

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
        MolerTest.info("Sleep for {:.2f} seconds.".format(seconds))
        time.sleep(seconds)
