# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import pytest
from moler.connection_observer import ConnectionObserver
from moler.exceptions import MolerStatusException
import time


def test_moler_test_not_raise_exception_when_steps_end(moler_test_se):
    ConnectionObserver.get_active_exceptions_in_time(0, time.time())
    moler_test_se.test_not_raise_exception_when_steps_end()


def test_moler_test_test_raise_exception_when_not_call_steps_end(moler_test_se):
    ConnectionObserver.get_active_exceptions_in_time(0, time.time())
    with pytest.raises(MolerStatusException):
        moler_test_se.test_raise_exception_when_not_call_steps_end()


def test_moler_test_raise_exception_when_log_error(moler_test_se):
    ConnectionObserver.get_active_exceptions_in_time(0, time.time())
    with pytest.raises(MolerStatusException):
        moler_test_se.test_raise_exception_when_log_error()


def test_moler_test_raise_exception_when_log_error_raise_exception_set(moler_test_se):
    ConnectionObserver.get_active_exceptions_in_time(0, time.time())
    with pytest.raises(MolerStatusException):
        moler_test_se.test_raise_exception_when_log_error_raise_exception_set()


def test_moler_test_not_raise_exception_when_no_steps_end(moler_test):
    ConnectionObserver.get_active_exceptions_in_time(0, time.time())
    moler_test.test_not_raise_exception_when_no_steps_end()

# --------------------------- resources ---------------------------

@pytest.yield_fixture
def moler_test_se():
    from moler.util.moler_test import MolerTest

    @MolerTest.moler_raise_background_exceptions_steps_end()
    class MolerTestExampleSE(object):
        def test_not_raise_exception_when_steps_end(self):
            MolerTest.log("Start MolerTest test with log and steps_end")

            MolerTest.steps_end()

        def test_raise_exception_when_not_call_steps_end(self):
            MolerTest.log("Start MolerTest test with log and without steps_end")

        def test_raise_exception_when_log_error(self):
            MolerTest.log_error("Start MolerTest test with log_error")

        def test_raise_exception_when_log_error_raise_exception_set(self):
            MolerTest.log_error("Start MolerTest test with log_error and raise_exception", raise_exception=True)

    yield MolerTestExampleSE()


@pytest.yield_fixture
def moler_test():
    from moler.util.moler_test import MolerTest

    @MolerTest.moler_raise_background_exceptions()
    class MolerTestExample(object):
        def test_not_raise_exception_when_no_steps_end(self):
            MolerTest.log("Start MolerTest test with log and steps_end")

    yield MolerTestExample()
