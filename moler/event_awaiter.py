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
    def await_all(timeout, events):
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
        return all_done

    @staticmethod
    def await_any(timeout, events, sleep=0.01):
        grand_timeout = timeout
        start_time = time.time()
        any_done = False
        while timeout >= 0:
            time.sleep(sleep)
            for event in events:
                if event.done():
                    any_done = True
                    break
            timeout = grand_timeout - (time.time() - start_time)
        return any_done

    @staticmethod
    def separate_done_events(events):
        done_events = list()
        not_done_events = list()
        for event in events:
            if event.done():
                done_events.append(event)
            else:
                not_done_events.append(event)
        return [done_events, not_done_events]
