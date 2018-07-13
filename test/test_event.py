# -*- coding: utf-8 -*-
"""
Testing command specific API

Event is a type of ConnectionObserver.
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import importlib

import pytest
from moler.event import Event
from moler.connection import ObservableConnection
from moler.helpers import instance_id


def test_event_has_means_to_retrieve_embedded_detect_pattern(do_nothing_command__for_major_base_class):
    event_instance = do_nothing_command__for_major_base_class
    assert hasattr(event_instance, "detect_pattern")
    assert hasattr(event_instance, "detect_patterns")


def test_str_conversion_of_event_object():
    class Wait4(Event):
        def __init__(self, connection=None):
            super(Wait4, self).__init__(connection=connection)
            self.detect_pattern = 'Connection close'

        def data_received(self, data):
            pass  # not important now

    wait4 = Wait4()
    assert 'Wait4("Connection close", id:{})'.format(instance_id(wait4)) == str(wait4)


def test_event_string_is_required_to_start_command(command_major_base_class):
    from moler.exceptions import NoDetectPatternProvided
    moler_conn = ObservableConnection()

    event_class = do_nothing_command_class(base_class=command_major_base_class)
    event = event_class(connection=moler_conn)
    assert not event.detect_pattern  # ensure it is empty before starting command
    assert not event.detect_patterns  # ensure it is empty before starting command

    with pytest.raises(NoDetectPatternProvided) as error:
        event.start()  # start the command-future (background run)


def test_event_is_running(do_nothing_command__for_major_base_class):
    wait4 = do_nothing_command__for_major_base_class

    class TheConnection(object):
        def subscribe(self, observer):
            pass

    wait4.connection = TheConnection()
    wait4.detect_pattern = 'Connection lose'
    assert not wait4.running()
    wait4.start()  # start the event-future


# --------------------------- resources ---------------------------


@pytest.fixture(params=['event.Event'])
def command_major_base_class(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module('moler.{}'.format(module_name))
    klass = getattr(module, class_name)
    return klass


def do_nothing_command_class(base_class):
    """Command class that can be instantiated (overwritten abstract methods); uses different base class"""
    class DoNothingCommand(base_class):
        def data_received(self, data):  # we need to overwrite it since it is @abstractmethod
            pass  # ignore incoming data
    return DoNothingCommand


@pytest.fixture
def do_nothing_command_class__for_major_base_class(command_major_base_class):
    klass = do_nothing_command_class(base_class=command_major_base_class)
    return klass


@pytest.fixture
def do_nothing_command__for_major_base_class(do_nothing_command_class__for_major_base_class):
    instance = do_nothing_command_class__for_major_base_class()
    return instance
