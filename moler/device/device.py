# -*- coding: utf-8 -*-
"""
Package Open Source functionality of Moler.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst, Tomasz Krol'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com, tomasz.krol@nokia.com'


from moler.config import devices as devices_config
from moler.instance_loader import create_instance_from_class_fullname
from moler.helpers import copy_list
from moler.exceptions import WrongUsage
from moler.helpers import copy_dict
from moler.helpers import compare_objects
from moler.util.moler_test import MolerTest
import six
import functools
import threading
import logging

logger = logging.getLogger("moler")


class DeviceFactory(object):
    _lock_device = threading.Lock()

    _devices = {}
    _devices_params = {}
    _unique_names = {}  # key is public_name, value is internal name (generated from public_name) unique for any
    # instance of device
    _already_used_names = set()
    _was_any_device_deleted = False

    @classmethod
    def was_any_device_deleted(cls):
        """
        Checks if any device was deleted.
        :return: True if any device was deleted, False otherwise
        """
        return cls._was_any_device_deleted

    @classmethod
    def create_all_devices(cls):
        """
        Creates all devices from config.

        :return: None
        """
        for device_name in devices_config.named_devices:
            cls.get_device(name=device_name)

    @classmethod
    def remove_all_devices(cls, clear_device_history=False):
        """
        Remove all created devices.

        :param clear_device_history: set True to clear the history of devices. Caution: you may overwrite your logs!
        :return: None
        """
        devices = copy_list(cls._devices.keys(), deep_copy=False)
        for device_name in devices:
            cls.remove_device(name=device_name)
        devices_config.clear()
        if clear_device_history:
            MolerTest.warning("All history of devices will be forgotten. The same names can be used again with"
                              " different meaning!")
            cls._clear()

    @classmethod
    def get_device(cls, name=None, device_class=None, connection_desc=None, connection_hops=None, initial_state=None,
                   establish_connection=True, lazy_cmds_events=None):
        """
        Return connection instance of given io_type/variant.

        :param name: name of device defined in configuration.
        :param device_class: 'moler.device.unixlocal.UnixLocal', 'moler.device.unixremote.UnixRemote', ...
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
        with cls._lock_device:
            dev = cls._get_device_without_lock(name=name, device_class=device_class, connection_desc=connection_desc,
                                               connection_hops=connection_hops, initial_state=initial_state,
                                               establish_connection=establish_connection,
                                               lazy_cmds_events=lazy_cmds_events)

        return dev

    @classmethod
    def remove_device(cls, name):
        """
        Removes device. All commands and events are being finished when device is removed.

        :param name: name of device..
        :return: None.
        """
        dev = cls.get_device(name=name)
        dev.remove()
        cls._was_any_device_deleted = True

    @classmethod
    def get_cloned_device(cls, source_device, new_name, initial_state=None, establish_connection=True,
                          lazy_cmds_events=False):
        """
        Creates (if necessary) and returns new device based on existed device.

        :param source_device: Reference to base device or name of base device.
        :param new_name: Name of new device.
        :param initial_state: Initial state of created device. If None then state of source device will be used.
        :param establish_connection: True to open connection, False if it does not matter.
        :return: Device object.
        """
        with cls._lock_device:
            logger.info('START creating device {} from {}'.format(new_name, source_device))
            source_device_name = source_device
            if isinstance(source_device, six.string_types):
                source_device = cls._get_device_without_lock(name=source_device, device_class=None,
                                                             connection_desc=None, connection_hops=None,
                                                             initial_state=None, establish_connection=True,
                                                             lazy_cmds_events=lazy_cmds_events)
                logger.info('STEP 1 - creating source device {}'.format(source_device_name))
            source_name = source_device.name  # name already translated to alias.
            if new_name in cls._devices.keys():
                cached_cloned_from = cls._devices_params[new_name]['cloned_from']
                if cached_cloned_from == source_name:
                    return cls._devices[new_name]
                else:
                    msg = "Attempt to create device '{}' as clone of '{}' but device with such name already created " \
                          "as clone of '{}'.".format(new_name, source_name, cached_cloned_from)
                    raise WrongUsage(msg)
            if initial_state is None:
                initial_state = source_device.current_state

            device_class = cls._devices_params[source_name]['class_fullname']
            constructor_parameters = cls._devices_params[source_name]['constructor_parameters']
            constructor_parameters["initial_state"] = initial_state
            if constructor_parameters["name"]:
                constructor_parameters["name"] = new_name
            logger.info('STEP 2 - creating cloned device {}'.format(new_name))
            dev = cls._create_instance_and_remember_it(
                device_class=device_class, constructor_parameters=constructor_parameters,
                establish_connection=establish_connection, name=new_name)
            new_name = dev.name
            cls._devices_params[new_name]['cloned_from'] = source_name
            logger.info('DONE creating device {} from {}'.format(new_name, source_device_name))
        return dev

    @classmethod
    def get_devices_by_type(cls, device_type):
        """
        Returns list of devices filtered by device_type.

        :param device_type: type of device. If None then return all devices.
        :return: List of devices. Can be an empty list.
        """
        with cls._lock_device:
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
    def _try_take_named_device_params(cls, name, device_class, connection_desc, connection_hops, initial_state,
                                      lazy_cmds_events):
        if name:
            if name not in devices_config.named_devices:
                whats_wrong = "was not defined inside configuration"
                raise KeyError("Device named '{}' {}".format(name, whats_wrong))
            cfg_device_class, cfg_connection_desc, cfg_connection_hops, cfg_initial_state, cfg_lazy_cmds_events = \
                devices_config.named_devices[name]
            device_class = cfg_device_class if device_class is None else device_class
            connection_desc = cfg_connection_desc if connection_desc is None else connection_desc
            connection_hops = cfg_connection_hops if connection_hops is None else connection_hops
            initial_state = cfg_initial_state if initial_state is None else initial_state
            lazy_cmds_events = cfg_lazy_cmds_events if lazy_cmds_events is None else lazy_cmds_events

        return device_class, connection_desc, connection_hops, initial_state, lazy_cmds_events

    @classmethod
    def _clear(cls):
        for device in cls._devices.values():
            del device
        cls._devices = {}
        cls._devices_params = {}
        cls._unique_names = {}  # key is alias, value is real name
        cls._already_used_names = set()
        cls._was_any_device_deleted = False

    @classmethod
    def _create_device(cls, name, device_class, connection_desc, connection_hops, initial_state, establish_connection,
                       lazy_cmds_events):
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
        device_class, connection_desc, connection_hops, initial_state, lazy_cmds_events = cls._try_take_named_device_params(
            name, device_class, connection_desc, connection_hops, initial_state, lazy_cmds_events)
        if device_class and (not connection_desc):
            connection_desc = cls._try_select_device_connection_desc(device_class, connection_desc)

        conn_desc = dict(connection_desc)
        io_type = conn_desc.pop("io_type")
        variant = conn_desc.pop("variant", None)
        constructor_parameters = {
            "name": name,
            "io_type": io_type,
            "variant": variant,
            "io_constructor_kwargs": conn_desc,
            "sm_params": connection_hops,
            "initial_state": initial_state,
            "lazy_cmds_events": lazy_cmds_events
        }
        dev = cls._create_instance_and_remember_it(
            device_class=device_class, constructor_parameters=constructor_parameters,
            establish_connection=establish_connection, name=name)
        return dev

    @classmethod
    def forget_device_handler(cls, device_name):
        """
        Function to call to forget device.

        :param device_name: Name of device
        :return: None
        """
        with cls._lock_device:
            if device_name in cls._devices_params:
                del cls._devices_params[device_name]
            if device_name in cls._devices:
                del cls._devices[device_name]
            if device_name in devices_config.named_devices:
                del devices_config.named_devices[device_name]
            cls._was_any_device_deleted = True

    @classmethod
    def differences_between_devices_descriptions(cls, already_device_name, requested_device_def):
        """
        Checks if two device description are the same.

        :param already_device_name: Name of device already created by Moler
        :param requested_device_def: Description od device provided to create. The name is the same as above.
        :return: Empty string if descriptions are the same, if not the string with differences.
        """
        already_created_device = cls.get_device(already_device_name, establish_connection=False)
        already_device_def = copy_dict(DeviceFactory._devices_params[already_created_device.name], True)

        different_msg = ""
        already_full_class = already_device_def['class_fullname']
        current_full_class = requested_device_def['DEVICE_CLASS']
        if already_full_class == current_full_class:
            default_hops = dict()
            already_hops = already_device_def['constructor_parameters']['sm_params'].get('CONNECTION_HOPS',
                                                                                         default_hops)
            current_hops = requested_device_def.get('CONNECTION_HOPS', default_hops)
            diff = compare_objects(already_hops, current_hops)
            if diff:
                different_msg = "Device '{}' already created with SM parameters: '{}' but now requested with SM" \
                                " params: {}. \nDiff: {}".format(already_device_name, already_hops, current_hops, diff)
        else:
            different_msg = "Device '{}' already created as instance of class '{}' and now requested as instance of " \
                            "class '{}'".format(already_device_name, already_full_class, current_full_class)
        return different_msg

    @classmethod
    def _create_instance_and_remember_it(cls, device_class, constructor_parameters, establish_connection, name):
        """
        Creates instance of device class.

        :param device_class: Full class name of device (with package)
        :param constructor_parameters: Constructor parameters of device
        :param establish_connection: True then connect to device immediately and change state. False to do not connect.
        :param name: Name of device.
        :return: Instance of device.
        """
        org_name = name
        if name:
            name = cls._calculate_unique_name(name=name)
            constructor_parameters['name'] = name
        device = create_instance_from_class_fullname(class_fullname=device_class,
                                                     constructor_parameters=constructor_parameters)
        if establish_connection:
            device.goto_state(state=device.initial_state)

        if not name:
            name = device.name
            org_name = name
        cls._devices[name] = device
        cls._devices_params[name] = dict()
        cls._devices_params[name]['class_fullname'] = device_class
        cls._devices_params[name]['constructor_parameters'] = constructor_parameters
        cls._devices_params[name]['cloned_from'] = None
        handler = functools.partial(cls.forget_device_handler, name)
        device.register_device_removal_callback(callback=handler)
        device.public_name = org_name
        return device

    @classmethod
    def _get_device_without_lock(cls, name, device_class, connection_desc, connection_hops, initial_state,
                                 establish_connection, lazy_cmds_events):
        new_name = cls._get_unique_name(name)
        if new_name in cls._devices.keys():
            dev = cls._devices[new_name]
            if initial_state:
                dev.goto_state(state=initial_state)
            elif establish_connection and not dev.has_established_connection():
                dev.goto_state(state=dev.initial_state)

        else:
            dev = cls._create_device(name=name, device_class=device_class, connection_desc=connection_desc,
                                     connection_hops=connection_hops, initial_state=initial_state,
                                     establish_connection=establish_connection, lazy_cmds_events=lazy_cmds_events)
        return dev

    @classmethod
    def _calculate_unique_name(cls, name):
        new_device_name = name
        if name in cls._unique_names:
            nr = 2
            while new_device_name in cls._already_used_names:
                new_device_name = "{}_{}".format(name, nr)
                nr += 1
        cls._unique_names[name] = new_device_name
        cls._already_used_names.add(new_device_name)
        return new_device_name

    @classmethod
    def _get_unique_name(cls, name):
        new_name = name
        if name in cls._unique_names:
            new_name = cls._unique_names[name]
        return new_name
