# -*- coding: utf-8 -*-
"""
Tests for sleep functions/classes.
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import time

from moler.sleep import Sleep


def test_sleep_for_threaded_variant():
    sleep_time = 1
    start_time = time.time()

    Sleep.sleep(sleep_time)

    stop_time = time.time()
    elapsed = stop_time - start_time

    assert round(elapsed) == sleep_time
