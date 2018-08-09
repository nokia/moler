# -*- coding: utf-8 -*-
"""
Event awaiter
"""


__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import time


class EventAwaiter(object):

    @staticmethod
    def wait_all(timeout, events):
        """
        Wait for all events are done or timeout occurs
        :param timeout: time in seconds
        :param events: list of events to check
        :return: True if all events are done, False otherwise
        """
        grand_timeout = timeout
        start_time = time.time()
        for event in events:
            timeout = grand_timeout - (time.time() - start_time)
            if time < 0:
                break
            event.await_done(timeout=timeout)
        all_done = True
        for event in events:
            if not event.done():
                all_done = False
                break
        return all_done

    @staticmethod
    def wait_any(timeout, events, interval=0.01):
        """
        :param timeout: time in seconds
        :param events: list of events to check
        :param interval: interval in seconds between checking events
        :return: True if any event is done, False otherwise
        """
        grand_timeout = timeout
        start_time = time.time()
        any_done = False
        while timeout >= 0:
            time.sleep(interval)
            for event in events:
                if event.done():
                    any_done = True
                    break
            timeout = grand_timeout - (time.time() - start_time)
        return any_done

    @staticmethod
    def separate_done_events(events):
        """
        :param events: list of events to check and separate
        :return: tuple. 0th element is list of done events, 1st element is list of non done events
        """
        done_events = list()
        not_done_events = list()
        for event in events:
            if event.done():
                done_events.append(event)
            else:
                not_done_events.append(event)
        return [done_events, not_done_events]
