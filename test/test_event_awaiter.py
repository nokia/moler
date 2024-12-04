# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.events.unix.wait4prompt import Wait4prompt
from moler.cmd.unix.pwd import Pwd
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
    assert EventAwaiter.wait_for_all(timeout=0.2, events=events) is True
    done, not_done = EventAwaiter.separate_done_events(events)
    assert 2 == len(done)
    assert 0 == len(not_done)
    assert type(EventAwaiter.separate_done_events(events)) is tuple
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


def test_start_command_after_event(buffer_connection):
    moler_connection = buffer_connection.moler_connection
    pattern = "aaa"
    event = Wait4prompt(connection=moler_connection, till_occurs_times=1, prompt=pattern)
    events = [event]
    buffer_connection.remote_inject_response(pattern)

    cmd_pwd1 = Pwd(connection=moler_connection)
    cmd_pwd2 = Pwd(connection=moler_connection)
    cmds = (cmd_pwd1, cmd_pwd2)
    EventAwaiter.start_command_after_event(events=events, cmds=cmds)
    assert cmd_pwd1.running() is True
    assert cmd_pwd2.running() is True
    assert event.running() is False
    assert event.done() is True
    EventAwaiter.cancel_all_events(events)
    EventAwaiter.cancel_all_events(cmds)


def test_start_command_after_event_with_sleep(buffer_connection):
    moler_connection = buffer_connection.moler_connection
    pattern = "aaa"
    event = Wait4prompt(connection=moler_connection, till_occurs_times=1, prompt=pattern)
    events = [event]
    buffer_connection.remote_inject_response(pattern)

    cmd_pwd1 = Pwd(connection=moler_connection)
    cmd_pwd2 = Pwd(connection=moler_connection)
    cmds = (cmd_pwd1, cmd_pwd2)
    EventAwaiter.start_command_after_event(events=events, cmds=cmds, sleep_after_event=0.3)
    assert cmd_pwd1.running() is True
    assert cmd_pwd2.running() is True
    assert event.running() is False
    assert event.done() is True
    EventAwaiter.cancel_all_events(events)
    EventAwaiter.cancel_all_events(cmds)
