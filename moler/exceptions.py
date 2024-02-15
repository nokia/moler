# -*- coding: utf-8 -*-
__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2023, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'


class MolerException(Exception):
    pass


class ParsingDone(MolerException):
    """
    Indicate that given part of output has been fully parsed
    and requires no further processing.
    """


class WrongUsage(MolerException):
    """Wrong usage of library"""


# TODO: do we need it? Just mapping to asyncio/concurrent.futures naming?
class CancelledError(MolerException):
    pass


class NoResultSinceCancelCalled(CancelledError):
    def __init__(self, connection_observer):
        """Create instance of NoResultSinceCancelCalled exception"""
        err_msg = f'for {connection_observer}'
        super(NoResultSinceCancelCalled, self).__init__(err_msg)
        self.connection_observer = connection_observer


# TODO: do we need it? Just mapping to asyncio naming?
class InvalidStateError(MolerException):
    pass


class ResultNotAvailableYet(InvalidStateError):
    def __init__(self, connection_observer):
        """Create instance of ResultNotAvailableYet exception"""
        err_msg = f'for {connection_observer}'
        super(ResultNotAvailableYet, self).__init__(err_msg)
        self.connection_observer = connection_observer


class ConnectionObserverNotStarted(InvalidStateError):
    def __init__(self, connection_observer):
        """Create instance of ConnectionObserverNotStarted exception"""
        err_msg = f'for {connection_observer}'
        super(ConnectionObserverNotStarted, self).__init__(err_msg)
        self.connection_observer = connection_observer


class ResultAlreadySet(InvalidStateError):
    def __init__(self, connection_observer):
        """Create instance of ResultAlreadySet exception"""
        err_msg = f'for {connection_observer}'
        super(ResultAlreadySet, self).__init__(err_msg)
        self.connection_observer = connection_observer


class MolerTimeout(MolerException):
    def __init__(self, timeout, kind='run', passed_time=0):
        """Create instance of MolerTimeout exception"""
        if passed_time and isinstance(passed_time, (int, float)):
            passed_time = f'{passed_time:.2f} '
        err_msg = f'{kind} time {passed_time}>= {timeout:.2f} sec'
        super(MolerTimeout, self).__init__(f"{err_msg} timeout")
        self.timeout = timeout


class ConnectionObserverTimeout(MolerTimeout):
    def __init__(self, connection_observer, timeout, kind='run', passed_time=''):
        """Create instance of ConnectionObserverTimeout exception"""
        super(ConnectionObserverTimeout, self).__init__(timeout=timeout,
                                                        kind=f'{connection_observer} {kind}',
                                                        passed_time=passed_time)
        self.connection_observer = connection_observer


class CommandTimeout(ConnectionObserverTimeout):
    pass


class NoCommandStringProvided(MolerException):
    def __init__(self, command):
        """Create instance of NoCommandStringProvided exception"""
        fix_info = 'fill .command_string member before starting command'
        err_msg = f'for {command}\nYou should {fix_info}'
        super(NoCommandStringProvided, self).__init__(err_msg)
        self.command = command


class NoDetectPatternProvided(MolerException):
    def __init__(self, command):
        """Create instance of NoDetectPatternProvided exception"""
        fix_info = 'fill .detect_patterns member before starting event'
        err_msg = f'for {command}\nYou should {fix_info}'
        super(NoDetectPatternProvided, self).__init__(err_msg)
        self.command = command


class NoConnectionProvided(MolerException):
    def __init__(self, connection_observer):
        """Create instance of NoConnectionProvided exception"""
        err_msg = f'for {connection_observer}'
        super(NoConnectionProvided, self).__init__(err_msg)
        self.connection_observer = connection_observer


class CommandFailure(MolerException):
    def __init__(self, command, message):
        err_msg = f"Command '{command.__class__.__module__}.{command.__class__.__name__}' ('{command.command_string}') failed with >>{message}<<."
        self.command = command
        super(CommandFailure, self).__init__(err_msg)


class CommandWrongState(MolerException):
    def __init__(self, command, expected_state, current_state):
        err_msg = f"Command '{command.command_string}' tried to run in state '{current_state}' but created in '{expected_state}'."
        self.command = command
        super(CommandWrongState, self).__init__(err_msg)


class EventWrongState(MolerException):
    def __init__(self, event, expected_state, current_state):
        err_msg = f"Event '{event.event_name}' tried to run in state '{current_state}' but created in '{expected_state}'."
        self.event = event
        super(EventWrongState, self).__init__(err_msg)


class ExecutionException(MolerException):
    def __init__(self, msg):
        super(ExecutionException, self).__init__(msg)


class DeviceFailure(MolerException):
    def __init__(self, device, message):
        self.device = device
        err_msg = f"Device '{device}' failed with '{message}'."
        super(DeviceFailure, self).__init__(err_msg)


class DeviceChangeStateFailure(DeviceFailure):
    def __init__(self, device, exception, device_name=None):
        if device_name is None:
            device_name = 'unknown name'
        self.device = device
        err_msg = f"Exception raised by device '{device}' ({device_name}) SM when try to changing state: '{exception}'."
        super(DeviceChangeStateFailure, self).__init__(device, err_msg)
