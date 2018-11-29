# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from moler.exceptions import WrongUsage
import threading


class Scheduler(object):

    @staticmethod
    def get_job(fun, interval, fun_params=None):
        """
        Static method to create job.
        :param fun: Reference to callable object (i.e. function, method)
        :param interval: time in float seconds when fun is called
        :param fun_params: dict of params of fun
        :return: Instance of Job.
        """

        instance = Scheduler._get_instance()
        job_internal = instance._scheduler.add_job(fun, 'interval', seconds=interval, kwargs=fun_params)
        job_internal.pause()
        job = Job(job_internal)
        return job

    @staticmethod
    def change_kind(scheduler_type=None):
        """
        Static method to change type of scheduler
        :param scheduler_type: type of new scheduler. Allowed thread (default) or asyncio. If None then default multi
            threading model will be used.
        :return: Nothing. If scheduler_type is not supported then it raises object of type moler.exceptions.WrongUsage
        """
        instance = Scheduler._get_instance()
        instance._swap_scheduler(scheduler_type)

    @staticmethod
    def _get_instance():
        """
        :return: Instance of scheduler
        """
        if Scheduler._object is None:
            Scheduler()
        return Scheduler._object

    _object = None
    _lock = threading.Lock()

    def __init__(self, scheduler_type=None):
        """
        :param scheduler_type: 'thread' or 'asyncio'
        """
        with Scheduler._lock:
            if Scheduler._object:
                raise WrongUsage("Scheduler object already created. Cannot create more than one instance.")
            super(Scheduler, self).__init__()
            self._scheduler_type = None
            self._scheduler = None
            self._swap_scheduler(scheduler_type)
            Scheduler._object = self

    def _swap_scheduler(self, new_scheduler_type):
        """
        :param new_scheduler_type: type of new scheduler. 'thread' or 'asyncio'. If None then default multi threading
            Moler model will be used.
        :return: Nothing
        """
        if new_scheduler_type is None:
            new_scheduler_type = 'thread'  # TODO: call method to detect default type of multi threading Moler model.
        scheduler = self._create_scheduler(new_scheduler_type)
        if self._scheduler and (self._scheduler != scheduler):
            self._scheduler.remove_all_jobs()
            self._scheduler.shutdown()
        self._scheduler = scheduler
        self._scheduler_type = new_scheduler_type

    def _create_scheduler(self, scheduler_type):
        """
        :param scheduler_type: type of new scheduler: 'thread' or 'asyncio'
        :return: instance of scheduler
        """
        if self._scheduler_type == scheduler_type:
            return self._scheduler
        if scheduler_type == 'thread':
            scheduler = BackgroundScheduler()
        elif scheduler_type == 'asyncio':
            scheduler = AsyncIOScheduler()
        else:
            raise WrongUsage("Wrong value of 'scheduler_type': '{}'. Allowed are 'thread' or 'asyncio'".format(scheduler_type))
        scheduler.start()
        return scheduler


class Job(object):

    def __init__(self, job):
        super(Job, self).__init__()
        self._job = job

    def start(self):
        """
        Method to start the job.
        :return: Nothing
        """
        self._job.resume()

    def stop(self):
        """
        Method to stop the job
        :return: Nothing
        """
        self._job.pause()
