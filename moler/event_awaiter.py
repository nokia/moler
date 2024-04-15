# -*- coding: utf-8 -*-
"""
Event awaiter
"""


__author__ = "Marcin Usielski"
__copyright__ = "Copyright (C) 2018-2024, Nokia"
__email__ = "marcin.usielski@nokia.com"

import time

from typing import Sequence
from moler.connection_observer import ConnectionObserver
from moler.util.moler_test import MolerTest
from moler.helpers import copy_list


class EventAwaiter:
    """
    A utility class for waiting and managing events.
    """

    @classmethod
    def wait_for_all(cls, timeout: float, events: Sequence, interval: float = 0.001) -> bool:
        """
        Wait for all events to be done or timeout occurs.

        :param timeout: Time in seconds to wait for all events to be done.
        :param events: List of events to check.
        :param interval: Interval in seconds between checking events.
        :return: True if all events are done, False otherwise.
        """
        grand_timeout = timeout
        start_time = time.monotonic()
        all_done = True
        while timeout >= 0:
            time.sleep(interval)
            all_done = True
            for event in events:
                if not event.done():
                    all_done = False
                    break
            if all_done:
                break
            timeout = grand_timeout - (time.monotonic() - start_time)
        return all_done

    @classmethod
    def wait_for_any(cls, timeout: float, events: Sequence, interval: float = 0.001) -> bool:
        """
        Wait for any event to complete within the specified timeout.

        :param timeout: The maximum time to wait in seconds.
        :param events: A list of events to check.
        :param interval: The interval in seconds between checking events.
        :return: True if any event is done, False otherwise.
        """
        grand_timeout = timeout
        start_time = time.monotonic()
        any_done = False
        while timeout >= 0 and not any_done:
            time.sleep(interval)
            for event in events:
                if event.done():
                    any_done = True
                    break
            timeout = grand_timeout - (time.monotonic() - start_time)
        return any_done

    @classmethod
    def separate_done_events(cls, events: Sequence) -> tuple:
        """
        Separate list of events into two lists: done events and non-done events.

        :param events: A list of events to check and separate.
        :return: A tuple containing two lists. The first element is a list of done events, and the second element is a list of non-done events.
        """
        done_events = []
        not_done_events = []
        for event in events:
            if event.done():
                done_events.append(event)
            else:
                not_done_events.append(event)
        return (done_events, not_done_events)

    @classmethod
    def cancel_all_events(cls, events: Sequence[ConnectionObserver]) -> None:
        """
        Cancel all events in the given list.

        :param events: list of events to cancel
        :return: None
        """
        for event in events:
            event.cancel()

    @classmethod
    def start_command_after_event(cls, cmds: Sequence, events: Sequence, event_timeout: float = 6., sleep_after_event: float = 0.) -> None:
        """
        Start the given commands and events sequentially. The next command starts when the previous event is done.
        Passed cmds and events can be lists of ConnectionObserver objects or lists of lists/tuples containing ConnectionObserver objects.

        Example 1:
            cmds = [cmd1, cmd2, cmd3]
            events = [event1, (event2, event3), event4]

        Example 2:
            cmds = [(cmd1, cmd2), cmd3, cmd4]
            events = [event1, event2]

        :param cmds: A list of commands to start.
        :param events: A list of events to start. If None, then the next command is started immediately.
        :param event_timeout: Timeout for each event.
        :param sleep_after_event: Time to sleep after every event.
        :return: None
        """
        events_cp = copy_list(events, deep_copy=False)
        for cmd in cmds:
            cmds_items = cmd
            if isinstance(cmd, ConnectionObserver):
                cmds_items = (cmd,)
            try:
                event = events_cp.pop(0)
            except IndexError:
                cmd.start()
            else:
                events_after_command = event
                if event is None:
                    events_after_command = ()
                elif isinstance(event, ConnectionObserver):
                    events_after_command = (event,)
                for event in events_after_command:
                    event.start()
                for cmd_item in cmds_items:
                    cmd_item.start()
                for event in events_after_command:
                    event.await_done(timeout=event_timeout)
                if sleep_after_event > 0.:
                    MolerTest.sleep(sleep_after_event)
