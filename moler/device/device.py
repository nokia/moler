# -*- coding: utf-8 -*-
"""
Package Open Source functionality of Moler.
"""
__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

from moler.config import devices as devices_config
from moler.instance_loader import create_instance_from_class_fullname
from moler.helpers import copy_list
from moler.exceptions import WrongUsage
import six


class DeviceFactory(object):
    _devices = {}
    _devices_params = {}

    @classmethod
    def create_all_devices(cls):
        for device_name in devices_config.named_devices:
            cls.get_device(name=device_name)

    @classmethod
    def get_device(cls, name=None, device_class=None, connection_desc=None, connection_hops=None, initial_state=None,
                   establish_connection=True):
        """
        Return connection instance of given io_type/variant.

        :param name: name of device defined in configuration.
        :param device_class: 'moler.device.unixlocal', 'moler.device.unixremote', ...
        :param connection_desc: 'io_type' and 'variant' of device connection.
        :param connection_hops: connection hops to create device SM.
        :param initial_state: initial state for device e.g. UNIX_REMOTE.
        :param establish_connection: True to open connection, False if it does not matter.
        :return: requested device.
        """
        if (not name) and (not device_class):
            raise WrongUsage("Provide either 'name' or 'device_class' parameter (none given)")
        if name and device_class:
            raise WrongUsage("Use either 'name' or 'device_class' parameter (not both)")

        if name in cls._devices.keys():
            dev = cls._devices[name]
            if establish_connection and not dev.is_established():
                dev.goto_state(state=dev.initial_state)
        else:
            dev = cls._create_device(name=name, device_class=device_class, connection_desc=connection_desc,
                                     connection_hops=connection_hops, initial_state=initial_state,
                                     establish_connection=establish_connection)
        return dev

    @classmethod
    def get_cloned_device(cls, source_device, new_name, initial_state=None, establish_connection=True):
        """
        Creates (if necessary) and returns new device based on existed device.

        :param source_device: Reference to base device or name of base device.
        :param new_name: Name of new device.
        :param initial_state: Initial state of created device. If None then state of source device will be used.
        :param establish_connection: True to open connection, False if it does not matter.
        :return: Device object.
        """
        if isinstance(source_device, six.string_types):
            source_name = source_device
            source_device = cls.get_device(name=source_name)
        source_name = source_device.name
        if new_name in cls._devices.keys():
            cached_cloned_from = cls._devices_params[new_name]['cloned_from']
            if cached_cloned_from == source_name:
                return cls._devices[new_name]
            else:
                msg = "Attempt to create device '{}' as clone of '{}' but device with such name already created as" \
                    " clone of '{}'.".format(new_name, source_name, cached_cloned_from)
                raise WrongUsage(msg)
        if initial_state is None:
            initial_state = source_device.current_state

        device_class = cls._devices_params[source_name]['class_fullname']
        constructor_parameters = cls._devices_params[source_name]['constructor_parameters']
        constructor_parameters["initial_state"] = initial_state
        if constructor_parameters["name"]:
            constructor_parameters["name"] = new_name
        dev = cls._create_instance_and_remember_it(
            device_class=device_class, constructor_parameters=constructor_parameters,
            establish_connection=establish_connection, name=new_name)
        cls._devices_params[new_name]['cloned_from'] = source_name
        return dev

    @classmethod
    def get_devices_by_type(cls, device_type):
        """
        Returns list of devices filtered by device_type.

        :param device_type: type of device. If None then return all devices.
        :return: List of devices. Can be an empty list.
        """
        if device_type is None:
            devices = copy_list(src=cls._devices.values(), deep_copy=False)
        else:
            devices = list()
            for device in cls._devices.values():
                if isinstance(device, device_type):
                    devices.append(device)
        return devices

    @classmethod
    def _try_select_device_connection_desc(cls, device_class, connection_desc):
        if connection_desc is None:
            connection_desc = devices_config.default_connection
        if connection_desc is None:
            whats_wrong = "No connection_desc selected"
            selection_method = "directly or via configuration"
            raise KeyError("{} ({}) for '{}' connection".format(whats_wrong,
                                                                selection_method,
                                                                device_class))
        return connection_desc

    @classmethod
    def _try_take_named_device_params(cls, name, device_class, connection_desc, connection_hops, initial_state):
        if name:
            if name not in devices_config.named_devices:
                whats_wrong = "was not defined inside configuration"
                raise KeyError("Device named '{}' {}".format(name, whats_wrong))
            device_class, connection_desc, connection_hops, initial_state = devices_config.named_devices[name]

        return device_class, connection_desc, connection_hops, initial_state

    @classmethod
    def _clear(cls):
        for device in cls._devices.values():
            del device
        cls._devices = {}
        cls._devices_params = {}

    @classmethod
    def _create_device(cls, name, device_class, connection_desc, connection_hops, initial_state, establish_connection):
        """
        Creates and returns connection instance of given io_type/variant.

        :param name: name of device defined in configuration.
        :param device_class: 'moler.device.unixlocal', 'moler.device.unixremote', ...
        :param connection_desc: 'io_type' and 'variant' of device connection.
        :param connection_hops: connection hops to create device SM.
        :param initial_state: initial state for device e.g. UNIX_REMOTE.
        :param establish_connection: True to open connection, False if it does not matter.
        :return: requested device.
        """
        if connection_hops is not None:
            if "CONNECTION_HOPS" not in connection_hops.keys():
                new_connection_hops = dict()
                new_connection_hops["CONNECTION_HOPS"] = connection_hops

                connection_hops = new_connection_hops

        if not establish_connection:
            initial_state = None
        device_class, connection_desc, connection_hops, initial_state = cls._try_take_named_device_params(
            name, device_class, connection_desc, connection_hops, initial_state)
        if device_class and (not connection_desc):
            connection_desc = cls._try_select_device_connection_desc(device_class, connection_desc)

        constructor_parameters = {
            "name": name,
            "io_type": connection_desc["io_type"],
            "variant": connection_desc["variant"],
            "sm_params": connection_hops,
            "initial_state": initial_state
        }
        dev = cls._create_instance_and_remember_it(
            device_class=device_class, constructor_parameters=constructor_parameters,
            establish_connection=establish_connection, name=name)
        return dev

    @classmethod
    def forget_device_handler(cls, device_name):
        if device_name in cls._devices_params:
            del cls._devices_params[device_name]
        if device_name in cls._devices:
            del cls._devices[device_name]
        if device_name in devices_config.named_devices:
            del devices_config.named_devices[device_name]

    @classmethod
    def _create_instance_and_remember_it(cls, device_class, constructor_parameters, establish_connection, name):
        device = create_instance_from_class_fullname(class_fullname=device_class,
                                                     constructor_parameters=constructor_parameters)
        if establish_connection:
            device.goto_state(state=device.initial_state)

        if not name:
            name = device.name
        cls._devices[name] = device
        cls._devices_params[name] = dict()
        cls._devices_params[name]['class_fullname'] = device_class
        cls._devices_params[name]['constructor_parameters'] = constructor_parameters
        cls._devices_params[name]['cloned_from'] = None
        device.register_handler_to_notify_to_forget_device(handler=cls.forget_device_handler)
        return device
