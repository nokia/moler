# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers import SchedulerNotRunningError
from moler.exceptions import WrongUsage


class Scheduler(object):
    _object = None

    def __init__(self, scheduler_type='thread'):
        super(Scheduler, self).__init__()
        self._scheduler_type = None
        self._scheduler = None
        self._swap_scheduler(scheduler_type)

    @staticmethod
    def _get_instance():
        if Scheduler._object is None:
            Scheduler._object = Scheduler()
        return Scheduler._object

    @staticmethod
    def get_job(fun, interval, fun_params=None):
        instance = Scheduler._get_instance()
        job_internal = instance._scheduler.add_job(fun, 'interval', seconds=interval, kwargs=fun_params)
        job_internal.pause()
        job = Job(job_internal)
        return job

    @staticmethod
    def change_kind(scheduler_type):
        instance = Scheduler._get_instance()
        instance._swap_scheduler(scheduler_type)

    def _swap_scheduler(self, new_scheduler_type):
        self._scheduler = self._create_scheduler(new_scheduler_type)
        self._scheduler_type = new_scheduler_type

    def _create_scheduler(self, scheduler_type):
        scheduler = self._scheduler
        if self._scheduler_type != scheduler_type:
            if scheduler_type == 'thread':
                scheduler = BackgroundScheduler()
            elif scheduler_type == 'asyncio':
                scheduler = AsyncIOScheduler()
            else:
                raise WrongUsage("Wrong value of 'scheduler_type': '{}'. Allowed are 'thread' or 'asyncio'")
        scheduler.start()
        return scheduler


class Job(object):

    def __init__(self, job):
        super(Job, self).__init__()
        self.job = job

    def start(self):
        try:
            self.job.resume()
        except SchedulerNotRunningError:
            pass

    def stop(self):
        self.job.pause()
