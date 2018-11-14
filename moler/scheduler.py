# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers import SchedulerNotRunningError


class Scheduler(object):
    _object = None

    def __init__(self, kind='interval'):
        super(Scheduler, self).__init__()
        self.kind = kind
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    @staticmethod
    def _get_instance():
        if Scheduler._object is None:
            Scheduler._object = Scheduler()
        return Scheduler._object

    @staticmethod
    def get_job(fun, interval, fun_params=None):
        instance = Scheduler._get_instance()
        job_internal = instance.add_job(fun, instance.kind, seconds=interval, kwargs=fun_params)
        job_internal.pause()
        job = Job(job_internal)
        return job


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
