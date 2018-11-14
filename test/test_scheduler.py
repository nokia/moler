# -*- coding: utf-8 -*-
"""
Testing of Scheduler.
"""
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.scheduler import Scheduler
from time import sleep


def test_job():
    values = {'number': 0}
    job = Scheduler.get_job(callback, 0.1, {'param_dict': values})
    job.start()
    sleep(0.22)
    job.stop()
    assert(2 == values['number'])


def test_2_jobs_concurrently():
    values_1 = {'number': 0}
    values_2 = {'number': 0}
    job1 = Scheduler.get_job(callback, 0.05, {'param_dict': values_1})
    job2 = Scheduler.get_job(callback, 0.10, {'param_dict': values_2})
    job1.start()
    job2.start()
    sleep(0.23)
    job1.stop()
    job2.stop()
    assert (2 == values_2['number'])
    assert (4 == values_1['number'])


def callback(param_dict):
    param_dict['number'] += 1
