# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.events.unix.wait4prompt import Wait4prompt
from moler.event_awaiter import EventAwaiter
from moler.threaded_moler_connection import ThreadedMolerConnection
import datetime


def test_events_true_all():
    connection = ThreadedMolerConnection()
    events = list()
    patterns = ("aaa", "bbb")
    for pattern in patterns:
        event = Wait4prompt(connection=connection, till_occurs_times=1, prompt=pattern)
        event.start()
        events.append(event)
        connection.data_received(pattern, datetime.datetime.now())
    assert EventAwaiter.wait_for_all(timeout=0.1, events=events) is True
    done, not_done = EventAwaiter.separate_done_events(events)
    assert 2 == len(done)
    assert 0 == len(not_done)
    EventAwaiter.cancel_all_events(events)


def test_events_false_all():
    connection = ThreadedMolerConnection()
    events = list()
    patterns = ("aaa", "bbb")
    for pattern in patterns:
        event = Wait4prompt(connection=connection, till_occurs_times=1, prompt=pattern)
        event.start()
        events.append(event)
    connection.data_received(patterns[0], datetime.datetime.now())
    assert EventAwaiter.wait_for_all(timeout=0.1, events=events) is False
    done, not_done = EventAwaiter.separate_done_events(events)
    assert 1 == len(done)
    assert 1 == len(not_done)
    EventAwaiter.cancel_all_events(events)


def test_events_true_any_all():
    connection = ThreadedMolerConnection()
    events = list()
    patterns = ("aaa", "bbb")
    for pattern in patterns:
        event = Wait4prompt(connection=connection, till_occurs_times=1, prompt=pattern)
        event.start()
        events.append(event)
        connection.data_received(pattern, datetime.datetime.now())
    assert EventAwaiter.wait_for_any(timeout=0.1, events=events) is True
    done, not_done = EventAwaiter.separate_done_events(events)
    assert len(done) >= 1
    assert len(not_done) <= 1
    EventAwaiter.cancel_all_events(events)


def test_events_true_any_one():
    connection = ThreadedMolerConnection()
    events = list()
    patterns = ("aaa", "bbb")
    for pattern in patterns:
        event = Wait4prompt(connection=connection, till_occurs_times=1, prompt=pattern)
        event.start()
        events.append(event)
    connection.data_received(patterns[0], datetime.datetime.now())
    assert EventAwaiter.wait_for_any(timeout=0.1, events=events) is True
    done, not_done = EventAwaiter.separate_done_events(events)
    assert 1 == len(done)
    assert 1 == len(not_done)
    EventAwaiter.cancel_all_events(events)


def test_events_false_any():
    connection = ThreadedMolerConnection()
    events = list()
    patterns = ("aaa", "bbb")
    for pattern in patterns:
        event = Wait4prompt(connection=connection, till_occurs_times=1, prompt=pattern)
        event.start()
        events.append(event)
    assert EventAwaiter.wait_for_any(timeout=0.1, events=events) is False
    done, not_done = EventAwaiter.separate_done_events(events)
    assert 0 == len(done)
    assert 2 == len(not_done)
    EventAwaiter.cancel_all_events(events)
