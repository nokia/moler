# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import time

import pytest

from moler.connection_observer import ConnectionObserver
from moler.exceptions import MolerStatusException
from moler.util.moler_test import MolerTest


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


def test_moler_test_raise_exception_when_no_steps_end_for_global_method():
    with pytest.raises(MolerStatusException):
        moler_test_raise_exception_when_no_steps_end_for_global_method()


# connection observer running in background thread may raise exception
# but such exception is not visible inside MainThread
# However, in all such cases connection observer stores exception via conn_obs.set_exception()


def test_exception_in_observer_is_raised_when_result_is_called_after_set_exception(do_nothing_connection_observer):
    exc = Exception("some error inside observer")

    def function_using_observer():
        observer = do_nothing_connection_observer
        # for real usage observer should be started to run background thread that will set_exception()
        # but for unit tests we just call it (simulating background thread)
        observer.set_exception(exc)
        print(observer.result())

    with pytest.raises(Exception) as err:
        function_using_observer()
    assert err.value == exc


def test_exception_in_observer_is_ignored_if_no_result_called_nor_decorator_on_function(do_nothing_connection_observer):
    def function_using_observer():
        observer = do_nothing_connection_observer
        observer.set_exception(Exception("some error inside observer"))

    function_using_observer()  # should not raise so test should pass


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


@MolerTest.moler_raise_background_exceptions_steps_end()
def moler_test_raise_exception_when_no_steps_end_for_global_method():
    MolerTest.log("Start global method with log and without steps_end")


@pytest.fixture
def do_nothing_connection_observer():
    from moler.connection_observer import ConnectionObserver

    class DoNothingObserver(ConnectionObserver):
        def data_received(self, data):  # we need to overwrite it since it is @abstractmethod
            pass  # ignore incoming data
    observer = DoNothingObserver()
    return observer
