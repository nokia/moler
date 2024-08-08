# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2021-2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import time

from moler.events.unix.wait4prompts import Wait4prompts
import datetime
import re


def test_split_lines(buffer_connection):
    prompts = {re.compile(r'moler_bash#'): "UNIX_LOCAL", re.compile(r'(root@|[\\w-]+).*?:.*#\\s+'): 'UNIX_LOCAL_ROOT'}
    outputs = [
        r"ls *_SYSLOG*.log" + chr(0x0D) + chr(0x0A),
        r"ls: ",
        r"cannot access '*_SYSLOG*.log' ",
        r": No such file or directory" + chr(0x0D) + chr(0x0A) + "moler_bash#"
    ]
    event = Wait4prompts(connection=buffer_connection.moler_connection, till_occurs_times=-1, prompts=prompts)
    event.check_against_all_prompts = True
    event._break_processing_when_found = False
    event._reverse_order = True
    was_callback_called = False
    error = None

    def _prompts_observer_callback(event):
        occurrence = event.get_last_occurrence()
        state = occurrence["state"]
        line = occurrence["line"]
        matched = occurrence["matched"]
        nonlocal was_callback_called
        was_callback_called = True
        try:
            assert state == "UNIX_LOCAL"
            assert line == "moler_bash#"
            assert matched == "moler_bash#"
        except AssertionError as err:
            nonlocal error
            error = err

    event.add_event_occurred_callback(callback=_prompts_observer_callback,
            callback_params={
                "event": event,
            },)
    event.start()
    for output in outputs:
        buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
        time.sleep(0.01)
    time.sleep(0.5)
    event.cancel()
    assert was_callback_called is True
    if error:
        raise error


def test_split_lines_char_by_char(buffer_connection):
    prompts = {re.compile(r'moler_bash#'): "UNIX_LOCAL", re.compile(r'(root@|[\\w-]+).*?:.*#\\s+'): 'UNIX_LOCAL_ROOT'}
    output = r"ls *_SYSLOG*.log" + chr(0x0D) + chr(0x0A) + "ls: cannot access '*_SYSLOG*.log': No such file or directory" + chr(0x0D) + chr(0x0A) + "moler_bash# "
    event = Wait4prompts(connection=buffer_connection.moler_connection, till_occurs_times=-1, prompts=prompts)
    event.check_against_all_prompts = True
    event._break_processing_when_found = False
    was_callback_called = False
    error = None

    def _prompts_observer_callback(event):
        occurrence = event.get_last_occurrence()
        state = occurrence["state"]
        line = occurrence["line"]
        matched = occurrence["matched"]
        nonlocal was_callback_called
        was_callback_called =True
        try:
            assert state == "UNIX_LOCAL"
            assert line == "moler_bash#"
            assert matched == "moler_bash#"
        except AssertionError as err:
            nonlocal error
            error = err

    event.add_event_occurred_callback(callback=_prompts_observer_callback,
            callback_params={
                "event": event,
            },)
    event.start()
    for char in output:
        buffer_connection.moler_connection.data_received(char.encode("utf-8"), datetime.datetime.now())
    time.sleep(0.5)
    event.cancel()
    assert was_callback_called is True
    if error:
        raise error


def test_event_wait4prompts_good_2_prompts_from_1_line(buffer_connection):
    prompts = {re.compile(r'host:.*#'): "UNIX_LOCAL", re.compile(r'user@server.*#'): "USER"}
    output = "user@host:/home/#"
    event = Wait4prompts(connection=buffer_connection.moler_connection, till_occurs_times=1, prompts=prompts)
    event.check_against_all_prompts = True
    event.start()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    ret = event.await_done(timeout=0.5)[0]
    assert event.done() is True
    assert 'list_matched' in ret
    assert 1 == len(ret['list_matched'])


def test_event_wait4prompts_change_prompts(buffer_connection):
    prompts = {re.compile(r'host:.*#'): "UNIX_LOCAL", re.compile(r'user@server.*#'): "USER"}
    output = "user@hoost:/home/#"
    event = Wait4prompts(connection=buffer_connection.moler_connection, till_occurs_times=1, prompts=prompts)
    event.check_against_all_prompts = True
    event.start()
    new_prompts = {re.compile(r'hoost:.*#'): "UNIX_LOCAL", re.compile(r'user@server.*#'): "USER"}
    event.change_prompts(prompts=new_prompts)
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    ret = event.await_done(timeout=0.5)[0]
    assert event.done() is True
    assert 'list_matched' in ret
    assert 1 == len(ret['list_matched'])


def test_event_wait4prompts_wrong_2_prompts_from_1_line(buffer_connection):
    prompts = {re.compile(r'host:.*#'): "UNIX_LOCAL", re.compile(r'user@.*#'): "USER"}
    output = "user@host:/home/#"
    event = Wait4prompts(connection=buffer_connection.moler_connection, till_occurs_times=1, prompts=prompts)
    event.check_against_all_prompts = True
    event.start()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    ret = event.await_done(timeout=0.5)[0]
    assert event.done() is True
    assert 'list_matched' in ret
    assert 2 == len(ret['list_matched'])


def test_event_wait4prompts_wrong_1_prompt_from_1_line(buffer_connection):
    prompts = {re.compile(r'host:.*#'): "UNIX_LOCAL", re.compile(r'user@.*#'): "USER"}
    output = "user@host:/home/#"
    event = Wait4prompts(connection=buffer_connection.moler_connection, till_occurs_times=1, prompts=prompts)
    event.check_against_all_prompts = False
    event.start()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    ret = event.await_done(timeout=0.5)[0]
    assert event.done() is True
    assert 'list_matched' not in ret


def test_event_wait4prompts_reverse_order(buffer_connection):
    matched_states = []

    def callback(w4p_event):
        occurrence = w4p_event.get_last_occurrence()
        state = occurrence["state"]
        matched_states.append(state)

    prompts = {re.compile(r'host:.*#'): "UNIX_LOCAL", re.compile(r'user@server.*#'): "USER"}
    output = "user@host:/home/#\nBLABLA\nuser@server:/home/#\n"
    event = Wait4prompts(connection=buffer_connection.moler_connection,
                         till_occurs_times=-1, prompts=prompts)
    event.add_event_occurred_callback(callback=callback, callback_params={"w4p_event": event})
    event._reverse_order = True
    event.start()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    start_time = time.monotonic()
    while 1 != len(matched_states) and time.monotonic() - start_time < 10:
        time.sleep(0.1)
    time.sleep(0.1)
    event.cancel()
    assert 1 == len(matched_states)
    assert 'USER' in matched_states


def test_event_wait4prompts_normal_order(buffer_connection):
    matched_states = []

    def callback(w4p_event):
        occurrence = w4p_event.get_last_occurrence()
        state = occurrence["state"]
        matched_states.append(state)

    prompts = {re.compile(r'host:.*#'): "UNIX_LOCAL", re.compile(r'user@server.*#'): "USER"}
    output = "user@host:/home/#\nBLABLA\nuser@server:/home/#\n"
    event = Wait4prompts(connection=buffer_connection.moler_connection,
                         till_occurs_times=-1, prompts=prompts)
    event._reverse_order = False
    event._break_processing_when_found = False
    event.add_event_occurred_callback(callback=callback, callback_params={"w4p_event": event})
    event.start()
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    start_time = time.monotonic()
    while 2 != len(matched_states) and time.monotonic() - start_time < 10:
        time.sleep(0.1)
    time.sleep(0.1)
    event.cancel()
    assert 2 == len(matched_states)
    assert matched_states == ['UNIX_LOCAL', 'USER']
