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

    @property
    @abc.abstractmethod
    def current_state(self):
        return self.state

    @abc.abstractmethod
    def is_established(self):
        pass

    @abc.abstractmethod
    def goto_state(self, state, timeout=-1, rerun=0, send_enter_after_changed_state=False,
                   log_stacktrace_on_fail=True):
        pass

    @abc.abstractmethod
    def establish_connection(self):
        pass

    @abc.abstractmethod
    def add_neighbour_device(self, neighbour_device, bidirectional=True):
        """
        Adds neighbour device to this device.

        :param neighbour_device: device object or string with device name.
        :param bidirectional: If True then this device will be added to f_device.
        :return: None
        """
        pass

    @abc.abstractmethod
    def get_neighbour_devices(self, device_type):
        """
        Returns list of neighbour devices of passed type.

        :param device_type: type of device. If None then all neighbour devices will be returned.
        :return: list of devices.
        """
        pass

    @abc.abstractmethod
    def configure_logger(self, name, propagate):
        pass

    @abc.abstractmethod
    def on_connection_made(self, connection):
        pass

    @abc.abstractmethod
    def on_connection_lost(self, connection):
        pass

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
        pass

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
        Wrapper for simple use:

        return ux.run('cd', path="/home/user/")

        Command/observer object is created locally
        """
        pass

    @abc.abstractmethod
    def start(self, cmd_name, **kwargs):
        """
        Wrapper for simple use:

        localhost_ping = ux.start('ping', destination="localhost", options="-c 5")
        ...
        result = localhost_ping.await_finish()

        result = await localhost_ping  # py3 notation

        Command/observer object is created locally
        """
        pass
