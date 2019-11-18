# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import six
import abc


@six.add_metaclass(abc.ABCMeta)
class AbstractDevice(object):

    def __init__(self):
        self._forget_handlers = list()

    @property
    @abc.abstractmethod
    def current_state(self):
        """
        Getter of current state.

        :return: String with the name of current state.
        """

    @property
    @abc.abstractmethod
    def name(self):
        """
        Getter of device name.

        :return: String with the device name.
        """

    @name.setter
    @abc.abstractmethod
    def name(self, value):
        """
        Setter for device name.

        :param value: String with device name.
        :return: None
        """

    @abc.abstractmethod
    def is_established(self):
        """
        Checks if connection is established to real device.

        :return: True if connection is established, False otherwise.
        """

    @abc.abstractmethod
    def goto_state(self, state, timeout=-1, rerun=0, send_enter_after_changed_state=False,
                   log_stacktrace_on_fail=True):
        """
        Goes to state.

        :param state: name of state to go.
        :param timeout: Time in seconds when break transitions if still not success.
        :param rerun: How many times try to rerun command(s) when device is still not in requested state.
        :param send_enter_after_changed_state: Set True to send enter after enters proper state.
        :param log_stacktrace_on_fail: Set True to log exceptions if command to enter state failed.
        :return: None
        """

    @abc.abstractmethod
    def establish_connection(self):
        """
        Establishes connection to real device.

        :return: None
        """

    @abc.abstractmethod
    def add_neighbour_device(self, neighbour_device, bidirectional=True):
        """
        Adds neighbour device to this device.

        :param neighbour_device: device object or string with device name.
        :param bidirectional: If True then this device will be added to f_device.
        :return: None
        """

    @abc.abstractmethod
    def get_neighbour_devices(self, device_type):
        """
        Returns list of neighbour devices of passed type.

        :param device_type: type of device. If None then all neighbour devices will be returned.
        :return: list of devices.
        """

    @abc.abstractmethod
    def configure_logger(self, name, propagate):
        """
        Configures logger.

        :param name: Name of logger
        :param propagate: Set True if you want to propagate logs, False otherwise (recommended)
        :return: None
        """

    @abc.abstractmethod
    def on_connection_made(self, connection):
        """
        Method to call by Moler framework when connection is established.

        :param connection: Connection object.
        :return: None
        """

    @abc.abstractmethod
    def on_connection_lost(self, connection):
        """
        Method to call by Moler framework when connection is lost.

        :param connection: Connection object.
        :return: None
        """

    @abc.abstractmethod
    def get_cmd(self, cmd_name, cmd_params=None, check_state=True, for_state=None):
        """
        Returns instance of command connected with the device.

        :param cmd_name: name of commands, name of class (without package), for example "cd".
        :param cmd_params: dict with command parameters.
        :param check_state: if True then before execute of command the state of device will be check if the same
         as when command was created. If False the device state is not checked.
        :param for_state: if None then command object for current state is returned, otherwise object for for_state is
         returned.
        :return: Instance of command
        """

    @abc.abstractmethod
    def get_event(self, event_name, event_params=None, check_state=True, for_state=None):
        """
        Return instance of event connected with the device.

        :param event_name: name of event, name of class (without package).
        :param event_params: dict with event parameters.
        :param check_state: if True then before execute of event the state of device will be check if the same
         as when event was created. If False the device state is not checked.
        :param for_state: if None then event object for current state is returned, otherwise object for for_state is
         returned.
        :return: Event object
        """

    @abc.abstractmethod
    def run(self, cmd_name, **kwargs):
        """
        Wrapper for simple use command: creates command, runs it and waits till it ends.

        :param cmd_name: name of class of command.
        :param kwargs: dict with parameters for command constructor.
        :return: object from command get_result (mainly dict).
        """

    @abc.abstractmethod
    def start(self, cmd_name, **kwargs):
        """
        Wrapper for simple use command: creates command and runs it.

        :param cmd_name: name of class of command.
        :param kwargs: dict with parameters for command constructor.
        :return: command object
        """

    def register_handler_to_notify_to_forget_device(self, handler):
        """
        Registers handler to notify when device should be forgot.

        :param handler: callable with parameter device_name to call when device should be forgot.
        :return: None
        """
        self._forget_handlers.append(handler)

    def close_and_forget(self):
        """
        Closes device, if any command or device is attached to this device they will be finished.

        :return: None
        """
        for handler in self._forget_handlers:
            handler()
