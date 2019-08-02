# -*- coding: utf-8 -*-
"""
Perform devices SM autotest.
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'michal.ernst@nokia.com'

import os
import random

from moler.device import DeviceFactory
from moler.device.textualdevice import TextualDevice
from moler.exceptions import MolerException
from moler.config import load_config
from moler.helpers import copy_list


def iterate_over_device_states(device):
    source_states = _get_all_states_from_device(device=device)
    target_states = copy_list(source_states)

    random.shuffle(source_states)
    random.shuffle(target_states)

    for source_state in source_states:
        for target_state in target_states:
            try:
                device.goto_state(source_state)
                device.goto_state(target_state)
            except Exception as exc:
                raise MolerException(
                    "Cannot trigger change state: '{}' -> '{}'\n{}".format(source_state, target_state, exc))


def get_device(name, connection, device_output, test_file_path):
    dir_path = os.path.dirname(os.path.realpath(test_file_path))
    load_config(os.path.join(dir_path, os.pardir, os.pardir, 'test', 'resources', 'device_config.yml'))

    device = DeviceFactory.get_device(name)
    device.io_connection = connection
    device.io_connection.name = device.name
    device.io_connection.moler_connection.name = device.name

    device.io_connection.remote_inject_response(device_output)
    device.io_connection.set_device(device)

    return device


def _get_all_states_from_device(device):
    states = copy_list(device.states)
    states.remove("NOT_CONNECTED")

    for attr_name in dir(device):
        attr = getattr(device, attr_name)
        if type(attr) is str and not attr_name.startswith('_') and attr_name not in dir(TextualDevice):
            if attr not in states:
                states.append(attr)

    if "PROXY_PC" in states and hasattr(device, "_use_proxy_pc") and not getattr(device, "_use_proxy_pc"):
        states.remove("PROXY_PC")

    return states
