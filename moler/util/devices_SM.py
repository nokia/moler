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
from moler.exceptions import MolerException
from moler.config import load_config
from moler.helpers import copy_list


def iterate_over_device_states(device):
    states = device.states

    states.remove("NOT_CONNECTED")

    source_states = copy_list(states)
    target_states = copy_list(states)

    random.shuffle(source_states)
    random.shuffle(target_states)

    print(states)
    print(len(states) * len(states))

    for source_state in source_states:
        for target_state in target_states:
            try:
                print('{} -> {}'.format(device.state, source_state))
                device.goto_state(source_state)
                print('{} -> {}'.format(source_state, target_state))
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
