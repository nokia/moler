# -*- coding: utf-8 -*-
"""
Perform devices SM autotest.
"""

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2021, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import os
import random
import time

from moler.device import DeviceFactory
from moler.device.textualdevice import TextualDevice
from moler.exceptions import MolerException
from moler.config import load_config
from moler.helpers import copy_list


def iterate_over_device_states(device, max_time=None):
    """
    Check all states in device under test.
    :param device: device
    :param max_time: maximum time of check. None for infinity. If execution time is greater then max_time then test is
     interrupted.
    :return: None
    """
    device.last_wrong_wait4_occurrence = None
    device.set_all_prompts_on_line(True)
    source_states = _get_all_states_from_device(device=device)
    target_states = copy_list(source_states)

    if len(source_states) > 5:
        device._goto_state_in_production_mode = False

    random.shuffle(source_states)
    random.shuffle(target_states)
    tested = set()

    start_time = time.time()
    for source_state in source_states:
        for target_state in target_states:
            current_test_str = "{}_{}".format(source_state, target_state)
            if current_test_str in tested:
                continue
            try:
                state_before_test = device.current_state
                device.goto_state(source_state, keep_state=False)
                tested.add("{}_{}".format(state_before_test, source_state))
                device.goto_state(target_state, keep_state=False)
                tested.add(current_test_str)
                if device.last_wrong_wait4_occurrence is not None:
                    raise MolerException("More than 1 prompt match the same line!: '{}'".format(
                        device.last_wrong_wait4_occurrence))
            except Exception as exc:
                raise MolerException(
                    "Cannot trigger change state: '{}' -> '{}'\n{}".format(source_state, target_state, exc))
            if max_time is not None and time.time() - start_time > max_time:
                return


def get_device(name, connection, device_output, test_file_path):
    dir_path = os.path.dirname(os.path.realpath(test_file_path))
    load_config(os.path.join(dir_path, os.pardir, os.pardir, 'test', 'resources', 'device_config.yml'))

    device = DeviceFactory.get_device(name)
    device.io_connection = connection
    device._prompts_event = None
    device.io_connection.name = device.name
    device.io_connection.moler_connection.name = device.name
    device._run_prompts_observers()

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
