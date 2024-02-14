from moler.util.connection_observer_life_status import ConnectionObserverLifeStatus

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'


def test_str():
    connection_observer_life_status = ConnectionObserverLifeStatus()
    expected_result = "ConnectionObserverLifeStatus(inactivity_timeout=0.0, last_feed_time=None, start_time=0.0, " \
                      "in_terminating=False, was_on_timeout_called=False, _is_running=False, terminating_timeout=0.0, " \
                      "timeout=20.0, is_done=False, is_cancelled=False)"
    result = str(connection_observer_life_status)
    assert result == expected_result


def test_str_values():
    connection_observer_life_status = ConnectionObserverLifeStatus()
    connection_observer_life_status.inactivity_timeout = 1.0
    connection_observer_life_status.last_feed_time = 2.0
    connection_observer_life_status.start_time = 3.0
    connection_observer_life_status.in_terminating = True
    connection_observer_life_status.was_on_timeout_called = True
    connection_observer_life_status._is_running = True
    connection_observer_life_status.terminating_timeout = 4.0
    connection_observer_life_status.timeout = 5.0
    connection_observer_life_status.is_done = True
    connection_observer_life_status.is_cancelled = True
    expected_result = "ConnectionObserverLifeStatus(inactivity_timeout=1.0, last_feed_time=2.0, start_time=3.0, " \
                      "in_terminating=True, was_on_timeout_called=True, _is_running=True, terminating_timeout=4.0, " \
                      "timeout=5.0, is_done=True, is_cancelled=True)"
    result = str(connection_observer_life_status)
    assert result == expected_result


def test_repr():
    connection_observer_life_status = ConnectionObserverLifeStatus()
    expected_result = "ConnectionObserverLifeStatus(inactivity_timeout=0.0, last_feed_time=None, start_time=0.0, " \
                      "in_terminating=False, was_on_timeout_called=False, _is_running=False, terminating_timeout=0.0, " \
                      "timeout=20.0, is_done=False, is_cancelled=False)"
    result = repr(connection_observer_life_status)
    assert result == expected_result


def test_repr_values():
    connection_observer_life_status = ConnectionObserverLifeStatus()
    connection_observer_life_status.inactivity_timeout = 1.0
    connection_observer_life_status.last_feed_time = 2.0
    connection_observer_life_status.start_time = 3.0
    connection_observer_life_status.in_terminating = True
    connection_observer_life_status.was_on_timeout_called = True
    connection_observer_life_status._is_running = True
    connection_observer_life_status.terminating_timeout = 4.0
    connection_observer_life_status.timeout = 5.0
    connection_observer_life_status.is_done = True
    connection_observer_life_status.is_cancelled = True
    expected_result = "ConnectionObserverLifeStatus(inactivity_timeout=1.0, last_feed_time=2.0, start_time=3.0, " \
                      "in_terminating=True, was_on_timeout_called=True, _is_running=True, terminating_timeout=4.0, " \
                      "timeout=5.0, is_done=True, is_cancelled=True)"
    result = repr(connection_observer_life_status)
    assert result == expected_result
