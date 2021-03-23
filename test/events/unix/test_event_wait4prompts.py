# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'


from moler.events.unix.wait4prompts import Wait4prompts
import datetime
import re


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
