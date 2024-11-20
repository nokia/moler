# -*- coding: utf-8 -*-
"""
Testing command specific API

Event is a type of ConnectionObserver.
"""

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import importlib
import datetime
import pytest

from moler.threaded_moler_connection import ThreadedMolerConnection
from moler.events.lineevent import LineEvent
from moler.helpers import instance_id
from moler.util.moler_test import MolerTest
from moler.exceptions import MolerException
from moler.exceptions import ResultAlreadySet


def test_event_has_means_to_retrieve_embedded_detect_pattern(lineevent_class):
    event_instance = lineevent_class(detect_patterns=[])
    assert hasattr(event_instance, "detect_patterns")


def test_str_conversion_of_event_object():
    class Wait4(LineEvent):
        def __init__(self, connection=None):
            super(Wait4, self).__init__(connection=connection, detect_patterns=['Connection close'])

        def data_received(self, data, recv_time):
            pass  # not important now

    wait4 = Wait4()
    assert f"Wait4(['Connection close'], id:{instance_id(wait4)})" == str(wait4)


def test_event_string_is_required_to_start_command(lineevent_class):
    from moler.exceptions import NoDetectPatternProvided
    moler_conn = ThreadedMolerConnection()

    event_class = do_nothing_connection_observer_class(base_class=lineevent_class)
    event = event_class(connection=moler_conn, detect_patterns=[])
    assert not event.detect_patterns  # ensure it is empty before starting command

    with pytest.raises(NoDetectPatternProvided) as error:
        event.start()  # start the command-future (background run)


def test_event_is_running(do_nothing_command__for_major_base_class):
    wait4 = do_nothing_command__for_major_base_class

    class TheConnection(object):
        def subscribe(self, observer, connection_closed_handler):
            pass

        def unsubscribe(self, observer, connection_closed_handler):
            pass

    wait4.connection = TheConnection()
    wait4.detect_patterns = ['Connection lose']
    assert not wait4.running()
    wait4.start()  # start the event-future
    assert wait4.running()
    wait4.cancel()


def test_event_cannot_assign_callback_when_assigned(buffer_connection):
    def fake_callback():
        pass

    def fake_callback2():
        pass

    from moler.events.unix.wait4prompt import Wait4prompt
    event = Wait4prompt(connection=buffer_connection.moler_connection, prompt="bash", till_occurs_times=1)
    event.add_event_occurred_callback(fake_callback, callback_params=dict())
    event.enable_log_occurrence()

    with pytest.raises(MolerException) as ex:
        event.add_event_occurred_callback(fake_callback)
    assert "is already assigned" in str(ex)
    with pytest.raises(MolerException) as ex:
        event.add_event_occurred_callback(fake_callback2)
    assert "is already assigned" in str(ex)

    event.remove_event_occurred_callback()
    event.add_event_occurred_callback(fake_callback2)

    ret = event.get_last_occurrence()
    assert ret is None


def test_event_output_in_parts(buffer_connection):
    from moler.events.unix.wait4prompt import Wait4prompt
    outputs = ["ba", "sh\n"]
    event = Wait4prompt(connection=buffer_connection.moler_connection, prompt="bash", till_occurs_times=1)
    event.start(timeout=0.1)
    for output in outputs:
        buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())

    event.await_done()
    assert event.done() is True
    with pytest.raises(ResultAlreadySet):
        event.event_occurred("data")


def test_event_whole_output(buffer_connection):
    from moler.events.unix.wait4prompt import Wait4prompt
    output = "bash\n"
    event = Wait4prompt(connection=buffer_connection.moler_connection, prompt="bash", till_occurs_times=1)
    event.start(timeout=0.1)
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    event.await_done()
    assert event.done() is True


def test_event_get_last_occurrence(buffer_connection):
    from moler.events.unix.wait4prompt import Wait4prompt
    output = "bash\n"
    dict_output = {'line': u'bash', 'matched': u'bash', 'named_groups': {}, 'groups': (), 'time': 0}
    event = Wait4prompt(connection=buffer_connection.moler_connection, prompt="bash", till_occurs_times=1)
    event.start(timeout=0.1)
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    event.await_done()
    occurrence = event.get_last_occurrence()
    occurrence['time'] = 0
    assert occurrence == dict_output


def test_event_unicode_error(buffer_connection):
    from moler.events.unix.wait4prompt import Wait4prompt

    class Wait4promptUnicodeError(Wait4prompt):
        def __init__(self, *args, **kwargs):
            self.raise_unicode = True
            self.nr = 0
            super(Wait4promptUnicodeError, self).__init__(*args, **kwargs)

        def on_new_line(self, line, is_full_line):
            if self.raise_unicode:
                self.nr += 1
                exc = UnicodeDecodeError("utf-8", b'abcdef', 0, 1, "Unknown")
                raise exc
            super(Wait4promptUnicodeError, self).on_new_line(line, is_full_line)

    timeout = 0.3
    output = "bash\n"
    dict_output = {'line': u'abcbash', 'matched': u'bash', 'named_groups': {}, 'groups': (), 'time': 0}
    event = Wait4promptUnicodeError(connection=buffer_connection.moler_connection, prompt="bash", till_occurs_times=1)
    event._ignore_unicode_errors = False
    event.raise_unicode = True
    event.start(timeout=timeout)
    buffer_connection.moler_connection.data_received("abc".encode("utf-8"), datetime.datetime.now())
    MolerTest.sleep(0.01)
    event.raise_unicode = False
    MolerTest.sleep(0.01)
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    with pytest.raises(MolerException):
        event.await_done()

    event = Wait4promptUnicodeError(connection=buffer_connection.moler_connection, prompt="bash", till_occurs_times=1)
    event._ignore_unicode_errors = True
    event.raise_unicode = True
    event.start(timeout=timeout)
    buffer_connection.moler_connection.data_received("abc".encode("utf-8"), datetime.datetime.now())
    MolerTest.sleep(0.01)
    event.raise_unicode = False
    buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    event.await_done()
    occurrence = event.get_last_occurrence()
    occurrence['time'] = 0
    assert occurrence == dict_output


def test_get_not_supported_parser():
    le = LineEvent(connection=None, detect_patterns=['Sample pattern'], match='not_supported_value')
    le._get_parser()

# --------------------------- resources ---------------------------


@pytest.fixture(params=['event.Event'])
def command_major_base_class(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module(f'moler.{module_name}')
    klass = getattr(module, class_name)
    return klass


@pytest.fixture(params=['events.lineevent.LineEvent'])
def lineevent_class(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module(f'moler.{module_name}')
    klass = getattr(module, class_name)
    return klass


def do_nothing_connection_observer_class(base_class):
    """Command class that can be instantiated (overwritten abstract methods); uses different base class"""

    class DoNothingConnectionObserver(base_class):
        def data_received(self, data, recv_time):  # we need to overwrite it since it is @abstractmethod
            pass  # ignore incoming data

        def pause(self):
            pass

        def resume(self):
            pass

    return DoNothingConnectionObserver


@pytest.fixture
def do_nothing_command_class__for_major_base_class(command_major_base_class):
    klass = do_nothing_connection_observer_class(base_class=command_major_base_class)
    return klass


@pytest.fixture
def do_nothing_command__for_major_base_class(do_nothing_command_class__for_major_base_class):
    instance = do_nothing_command_class__for_major_base_class()
    return instance
