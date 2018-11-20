# -*- coding: utf-8 -*-
"""
Testing of Scheduler.
"""
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.scheduler import Scheduler
from moler.exceptions import WrongUsage
from time import sleep
import pytest

try:
    import asyncio
except ImportError:  # pragma: nocover
    try:
        import trollius as asyncio
    except ImportError:
        raise ImportError(
            'Support for asyncio requires either Python 3.4 or the asyncio package installed or trollius installed for python 2.7')


def test_job():
    values = {'number': 0}
    job = Scheduler.get_job(callback, 0.1, {'param_dict': values})
    job.start()
    sleep(0.22)
    job.stop()
    assert(2 == values['number'])


def test_wrong_usage():
    with pytest.raises(WrongUsage):
        Scheduler.change_kind('wrong_kind')


def test_job_callback_as_method():
    values = {'number': 0}
    obj = TestCallback()
    job = Scheduler.get_job(obj.callback_method, 0.1, {'param_dict': values})
    job.start()
    sleep(0.22)
    job.stop()
    assert(2 == values['number'])
    assert(2 == obj.counter)


def test_2_jobs_concurrently():
    values_1 = {'number': 0}
    values_2 = {'number': 0}
    job1 = Scheduler.get_job(callback, 0.05, {'param_dict': values_1})
    job2 = Scheduler.get_job(callback, 0.10, {'param_dict': values_2})
    job1.stop()
    job1.start()
    job1.start()
    job2.start()
    sleep(0.23)
    job1.stop()
    job1.stop()
    job2.stop()
    assert (2 == values_2['number'])
    assert (4 == values_1['number'])


def test_asyncio_test_job():
    loop = asyncio.get_event_loop()
    Scheduler.change_kind("asyncio")
    values = {'number': 0}
    job = Scheduler.get_job(callback, 0.1, {'param_dict': values})
    job.start()
    loop.run_until_complete(asyncio.sleep(0.23))
    job.stop()
    loop.stop()
    Scheduler.change_kind("thread")
    assert (2 == values['number'])


def test_cannot_create_more_objects():
    with pytest.raises(WrongUsage):
        Scheduler()
        Scheduler()

def callback(param_dict):
    param_dict['number'] += 1


class TestCallback(object):
    def __init__(self):
        super(TestCallback, self).__init__()
        self.counter = 0

    def callback_method(self, param_dict):
        param_dict['number'] += 1
        self.counter += 1
