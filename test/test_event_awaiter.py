# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.events.unix.wait4prompt import Wait4prompt
from moler.event_awaiter import EventAwaiter
from moler.connection import ObservableConnection


def test_events_true_all():
    connection = ObservableConnection()
    events = list()
    patterns = ("aaa", "bbb")
    for pattern in patterns:
        event = Wait4prompt(connection=connection, till_occurs_times=1, prompt=pattern)
        event.start()
        events.append(event)
        connection.data_received(pattern)
    assert EventAwaiter.wait_for_all(timeout=0.1, events=events) is True
    done, not_done = EventAwaiter.separate_done_events(events)
    assert 2 == len(done)
    assert 0 == len(not_done)
    EventAwaiter.cancel_all_events(events)


def test_events_false_all():
    connection = ObservableConnection()
    events = list()
    patterns = ("aaa", "bbb")
    for pattern in patterns:
        event = Wait4prompt(connection=connection, till_occurs_times=1, prompt=pattern)
        event.start()
        events.append(event)
    connection.data_received(patterns[0])
    assert EventAwaiter.wait_for_all(timeout=0.1, events=events) is False
    done, not_done = EventAwaiter.separate_done_events(events)
    assert 1 == len(done)
    assert 1 == len(not_done)
    EventAwaiter.cancel_all_events(events)


def test_events_true_any_all():
    connection = ObservableConnection()
    events = list()
    patterns = ("aaa", "bbb")
    for pattern in patterns:
        event = Wait4prompt(connection=connection, till_occurs_times=1, prompt=pattern)
        event.start()
        events.append(event)
        connection.data_received(pattern)
    assert EventAwaiter.wait_for_any(timeout=0.1, events=events) is True
    done, not_done = EventAwaiter.separate_done_events(events)
    assert 2 == len(done)
    assert 0 == len(not_done)
    EventAwaiter.cancel_all_events(events)


def test_events_true_any_one():
    connection = ObservableConnection()
    events = list()
    patterns = ("aaa", "bbb")
    for pattern in patterns:
        event = Wait4prompt(connection=connection, till_occurs_times=1, prompt=pattern)
        event.start()
        events.append(event)
    connection.data_received(patterns[0])
    assert EventAwaiter.wait_for_any(timeout=0.1, events=events) is True
    done, not_done = EventAwaiter.separate_done_events(events)
    assert 1 == len(done)
    assert 1 == len(not_done)
    EventAwaiter.cancel_all_events(events)


def test_events_false_any():
    connection = ObservableConnection()
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
