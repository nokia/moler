# -*- coding: utf-8 -*-
"""
Testing of Scheduler.
"""
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.scheduler import Scheduler
from time import sleep


def test_interval():
    values = {'number': 0}
    job = Scheduler.get_job(callback, 0.1, {'param_dict': values})
    job.start()
    sleep(0.25)
    job.stop()
    assert(2 == values['number'])


def callback(param_dict):
    param_dict['number'] += 1
