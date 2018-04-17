# -*- coding: utf-8 -*-
__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


class MolerException(Exception):
    pass


class ParsingDone(MolerException):
    """
    Indicate that given part of output has been fully parsed
    and requires no further processing.
    """
    pass


class WrongUsage(MolerException):
    """Wrong usage of library"""
    pass


# TODO: do we need it? Just mapping to asyncio/concurrent.futures naming?
class CancelledError(MolerException):
    pass


class NoResultSinceCancelCalled(CancelledError):
    def __init__(self, connection_observer):
        """Create instance of NoResultSinceCancelCalled exception"""
        err_msg = 'for {}'.format(connection_observer)
        super(NoResultSinceCancelCalled, self).__init__(err_msg)
        self.connection_observer = connection_observer


# TODO: do we need it? Just mapping to asyncio naming?
class InvalidStateError(MolerException):
    pass


class ResultNotAvailableYet(InvalidStateError):
    def __init__(self, connection_observer):
        """Create instance of ResultNotAvailableYet exception"""
        err_msg = 'for {}'.format(connection_observer)
        super(ResultNotAvailableYet, self).__init__(err_msg)
        self.connection_observer = connection_observer


class ConnectionObserverNotStarted(InvalidStateError):
    def __init__(self, connection_observer):
        """Create instance of ConnectionObserverNotStarted exception"""
        err_msg = 'for {}'.format(connection_observer)
        super(ConnectionObserverNotStarted, self).__init__(err_msg)
        self.connection_observer = connection_observer


class ResultAlreadySet(InvalidStateError):
    def __init__(self, connection_observer):
        """Create instance of ResultAlreadySet exception"""
        err_msg = 'for {}'.format(connection_observer)
        super(ResultAlreadySet, self).__init__(err_msg)
        self.connection_observer = connection_observer


class ConnectionObserverTimeout(MolerException):
    def __init__(self, connection_observer, timeout,
                 kind='run', passed_time=''):
        """Create instance of ConnectionObserverTimeout exception"""
        if passed_time:
            passed_time = '{:.2f} '.format(passed_time)
        err_msg = '{} {} time {}>= {:.2f} sec'.format(connection_observer, kind,
                                                      passed_time, timeout)
        super(ConnectionObserverTimeout, self).__init__(err_msg + ' timeout')
        self.connection_observer = connection_observer
        self.timeout = timeout


class NoCommandStringProvided(MolerException):
    def __init__(self, command):
        """Create instance of NoCommandStringProvided exception"""
        fix_info = 'fill .command_string member before starting command'
        err_msg = 'for {}\nYou should {}'.format(command, fix_info)
        super(NoCommandStringProvided, self).__init__(err_msg)
        self.command = command


class NoConnectionProvided(MolerException):
    def __init__(self, connection_observer):
        """Create instance of NoConnectionProvided exception"""
        err_msg = 'for {}'.format(connection_observer)
        super(NoConnectionProvided, self).__init__(err_msg)
        self.connection_observer = connection_observer


class CommandFailure(MolerException):
    def __init__(self, command, message):
        err_msg = "Command failed '{}' with {}".format(command.command_string, message)
        self.command = command
        super(CommandFailure, self).__init__(err_msg)


class CommandTimeout(ConnectionObserverTimeout):
    pass
