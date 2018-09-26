# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import pytest

from moler.exceptions import MolerException


def test_moler_test_not_raise_exception_when_steps_end(moler_test):
    moler_test.test_not_raise_exception_when_steps_end()


def test_moler_test_raise_exception_when_log_error(moler_test):
    with pytest.raises(AssertionError):
        moler_test.test_raise_exception_when_log_error()


def test_moler_test_raise_exception_when_log_error_raise_exception_set(moler_test):
    with pytest.raises(MolerException):
        moler_test.test_raise_exception_when_log_error_raise_exception_set()


def test_moler_test_test_raise_exception_when_not_call_steps_end(moler_test):
    with pytest.raises(AssertionError):
        moler_test.test_raise_exception_when_not_call_steps_end()


# --------------------------- resources ---------------------------

@pytest.yield_fixture
def moler_test():
    from moler.util.moler_test import MolerTest

    @MolerTest.moler_test_status()
    class MolerTestExample(object):
        def test_not_raise_exception_when_steps_end(self):
            MolerTest.log("Start MolerTest test with log and steps_end")

            MolerTest.steps_end()

        def test_raise_exception_when_not_call_steps_end(self):
            MolerTest.log("Start MolerTest test with log and without steps_end")

        def test_raise_exception_when_log_error(self):
            MolerTest.log_error("Start MolerTest test with log_error")

        def test_raise_exception_when_log_error_raise_exception_set(self):
            MolerTest.log_error("Start MolerTest test with log_error and raise_exception", raise_exception=True)

    moler_test = MolerTestExample()
    yield moler_test
