# -*- coding: utf-8 -*-
"""
Perform devices SM autotest.
"""

__author__ = "Michal Ernst, Marcin Usielski"
__copyright__ = "Copyright (C) 2019-2024, Nokia"
__email__ = "michal.ernst@nokia.com, marcin.usielski@nokia.com"

import math
import os
import queue
import random
import threading
import time

from moler.config import load_config
from moler.device import DeviceFactory
from moler.device.textualdevice import TextualDevice
from moler.exceptions import MolerException
from moler.helpers import copy_list
from moler.io.raw.memory import ThreadedFifoBuffer
from moler.util.moler_test import MolerTest


def iterate_over_device_states(
    device,
    max_time=None,
    tests_per_device=300,
    max_no_of_threads=11,
    rerun=0,
    timeout_multiply=3.0,
    sleep_after_changed_state=0.0,
    states_to_skip=None,
):
    """
    Check all states in device under test.

    :param device: device
    :param max_time: maximum time of check. None for infinity. If execution time is greater then max_time then test is
     interrupted.
    :param tests_per_device: how many tests should be performed in one thread.
    :param max_no_of_threads: maximum number of threads that can be started.
    :param rerun: rerun for goto_state
    :param timeout_multiply: timeout_multiply for goto_state
    :param sleep_after_changed_state: sleep after state change
    :param states_to_skip: list of states to skip and not test. If None then all states are tested.
    :return: None
    """
    source_states = _get_all_states_from_device(device=device)
    if states_to_skip is not None:
        source_states = [state for state in source_states if state not in states_to_skip]
    target_states = copy_list(source_states)
    nr_of_tests = len(source_states) * len(target_states)

    device.last_wrong_wait4_occurrence = None
    device.set_all_prompts_on_line(True)

    device._goto_state_in_production_mode = False  # pylint: disable=protected-access
    device.goto_state(state=source_states[0], rerun=rerun, sleep_after_changed_state=sleep_after_changed_state)

    random.shuffle(source_states)
    random.shuffle(target_states)
    tested = set()

    states_to_test = queue.Queue(maxsize=nr_of_tests)
    for source in source_states:
        for target in target_states:
            states_to_test.put([source, target])
    assert states_to_test.qsize() == nr_of_tests

    nr_of_threads = math.ceil(nr_of_tests / float(tests_per_device))
    if nr_of_threads > max_no_of_threads:
        nr_of_threads = max_no_of_threads
    thread_nr = 1
    test_threads = []
    exceptions = []
    while thread_nr < nr_of_threads:
        new_connection = get_memory_device_connection()
        new_connection.open()
        new_device_name = f"{device.name}_C{thread_nr}"
        th = _perform_device_tests_start_thread(
            source_device=device,
            tested=tested,
            states_to_test=states_to_test,
            max_time=max_time,
            new_device_name=new_device_name,
            connection=new_connection,
            exceptions=exceptions,
            rerun=rerun,
            timeout_multiply=timeout_multiply,
            sleep_after_changed_state=sleep_after_changed_state
        )
        test_threads.append((th, new_connection))
        thread_nr += 1
    _perform_device_tests(
        device=device,
        tested=tested,
        states_to_test=states_to_test,
        max_time=max_time,
        rerun=rerun,
        timeout_multiply=timeout_multiply,
        sleep_after_changed_state=sleep_after_changed_state
    )
    for th, dev_connection in test_threads:
        th.join()
        dev_connection.close()
    if max_time is None:
        assert 0 == states_to_test.qsize()
    for ex in exceptions:
        print(f"ex: '{ex}' -> '{repr(ex)}'.")
    assert 0 == len(exceptions)


def _perform_device_tests_start_thread(
    source_device,
    tested,
    states_to_test,
    max_time,
    new_device_name,
    connection,
    exceptions,
    rerun,
    timeout_multiply,
    sleep_after_changed_state,
):
    try:
        th = threading.Thread(
            target=_start_device_tests,
            args=(
                source_device,
                tested,
                states_to_test,
                max_time,
                new_device_name,
                connection,
                exceptions,
                rerun,
                timeout_multiply,
                sleep_after_changed_state,
            ),
        )
        th.daemon = True
        th.start()
        return th
    except Exception as ex:
        exceptions.append(ex)
        MolerTest.info(f"exception: '{ex}' -> '{repr(ex)}'")


def _start_device_tests(
    source_device,
    tested,
    states_to_test,
    max_time,
    new_device_name,
    connection,
    exceptions,
    rerun,
    timeout_multiply,
    sleep_after_changed_state
):
    try:
        device = get_cloned_device(
            src_device=source_device,
            new_name=new_device_name,
            new_connection=connection,
        )
        device.goto_state(state=states_to_test.queue[0][0], rerun=rerun, sleep_after_changed_state=sleep_after_changed_state)
        _perform_device_tests(
            device=device,
            tested=tested,
            states_to_test=states_to_test,
            max_time=max_time,
            rerun=rerun,
            timeout_multiply=timeout_multiply,
            sleep_after_changed_state=sleep_after_changed_state
        )
    except Exception as ex:
        exceptions.append(ex)
        MolerTest.info(f"exception: '{ex}' -> '{repr(ex)}'")


def _perform_device_tests(
    device, tested, states_to_test, max_time, rerun, timeout_multiply, sleep_after_changed_state
):
    device.set_all_prompts_on_line(True)
    start_time = time.monotonic()
    test_nr = 0
    while 0 < states_to_test.qsize():
        source_state, target_state = states_to_test.get(0)
        if (source_state, target_state) in tested:
            continue
        try:
            state_before_test = device.current_state
            device.goto_state(
                source_state,
                keep_state=False,
                rerun=rerun,
                timeout_multiply=timeout_multiply,
                sleep_after_changed_state=sleep_after_changed_state,
            )
            tested.add((state_before_test, source_state))
            device.goto_state(
                target_state,
                keep_state=False,
                rerun=rerun,
                timeout_multiply=timeout_multiply,
                sleep_after_changed_state=sleep_after_changed_state,
            )
            tested.add((source_state, target_state))

            if device.last_wrong_wait4_occurrence is not None:
                prompts = [{item["state"]: item["prompt_regex"]} for item in
                           device.last_wrong_wait4_occurrence["list_matched"]]
                msg = f"More than 1 prompt match the same line!: {prompts} in line '{device.last_wrong_wait4_occurrence['line']}' '{device.last_wrong_wait4_occurrence}' in change state '{state_before_test}' -> '{source_state}' -> '{target_state}'"
                raise MolerException(msg)
        except Exception as exc:
            raise MolerException(
                f"Cannot trigger change state: '{source_state}' -> '{target_state}'. Successful tests: {test_nr}\n{exc}\nAlready tested '{tested}'."
            ) from exc
        test_nr += 1
        if max_time is not None and time.monotonic() - start_time > max_time:
            return


def get_device(name, connection, device_output, test_file_path):
    dir_path = os.path.dirname(os.path.realpath(test_file_path))
    load_config(
        os.path.join(
            dir_path, os.pardir, os.pardir, "test", "resources", "device_config.yml"
        )
    )
    device = DeviceFactory.get_device(name, io_connection=connection)
    _prepare_device(device=device, connection=connection, device_output=device_output)
    return device


def _prepare_device(device, connection, device_output):
    if connection != device.io_connection:
        device.exchange_io_connection(io_connection=connection)
    assert "RemoteConnection" in device.io_connection.__class__.__name__
    connection.send_last_prompt_on_error = True
    connection.set_device(device=device)
    device.set_all_prompts_on_line(True)
    device.io_connection.remote_inject_response(device_output)
    assert device.io_connection.data == device_output
    if device._prompts_event is None:  # pylint: disable=protected-access
        device._run_prompts_observers()  # pylint: disable=protected-access
    assert device._check_all_prompts_on_line is True  # pylint: disable=protected-access
    assert device._prompts_event.check_against_all_prompts is True  # pylint: disable=protected-access
    connection.open()
    if device.current_state == "NOT_CONNECTED":
        if device._established is True:  # pylint: disable=protected-access
            device._established = False  # pylint: disable=protected-access
        device.establish_connection()

    assert device.current_state != "NOT_CONNECTED"


def get_cloned_device(src_device, new_name, new_connection):
    device_output = src_device.io_connection.data
    device = DeviceFactory.get_cloned_device(
        source_device=src_device,
        new_name=new_name,
        establish_connection=False,
        lazy_cmds_events=True,
        io_connection=new_connection,
    )
    _prepare_device(
        device=device, connection=new_connection, device_output=device_output
    )
    return device


class RemoteConnection(ThreadedFifoBuffer):
    def __init__(self, moler_connection, echo=True, name=None, logger_name=""):
        self.device = None
        self.data = None
        self.input_bytes = None
        self.send_last_prompt_on_error = False
        self._last_prompt = "".encode("utf-8")
        super(RemoteConnection, self).__init__(
            moler_connection=moler_connection,
            echo=echo,
            name=name,
            logger_name=logger_name,
        )

    def remote_inject_response(self, input_strings):
        """
        Simulate remote endpoint that sends response.
        Response is given as strings.
        """
        self.data = input_strings

    def _inject_deferred(self):
        """
        Inject response on connection.
        """
        if self.device.state == "NOT_CONNECTED":
            raise MolerException(
                f"Device '{self.device.name}' in unsupported state '{self.device.state}'."
            )
        cmd_data_string = self.input_bytes.decode("utf-8")
        if cmd_data_string:
            if "\n" in cmd_data_string:
                cmd_data_string = cmd_data_string[:-1]  # remove \n from command_string on connection
        else:
            cmd_data_string = self.input_bytes

        try:
            binary_cmd_ret = self.data[self.device.state][cmd_data_string].encode(
                "utf-8"
            )
            self._last_prompt = binary_cmd_ret
            self.inject([self.input_bytes + binary_cmd_ret])
        except KeyError as exc:
            if self.send_last_prompt_on_error and (cmd_data_string == "\x03"):  # ctrl+c
                self.inject([self.input_bytes + self._last_prompt])
                return
            try:
                available_outputs = self.data[self.device.state].keys()
            except (KeyError, AttributeError):
                available_outputs = f"No output for state '{self.device.state}'. Data: '{self.data}'."
            raise MolerException(
                f"No output for cmd: '{cmd_data_string}' in state '{self.device.state}'!\n"
                f"Available outputs for the state: '{available_outputs}'.\n"
                "Please update your device_output dict!\n"
                f"{exc}"
            ) from exc

    def write(self, input_bytes):
        """
        What is written to connection comes back on read()
        only if we simulate echo service of remote end.
        """
        if self.echo:
            self.inject([input_bytes])

        self.input_bytes = input_bytes
        self._inject_deferred()

    def set_device(self, device):
        """
        Need to get actual state of device when sending cmds response.
        """
        self.device = device

    send = write  # just alias to make base class happy :-)


def get_memory_device_connection():
    from moler.config.loggers import configure_device_logger
    from moler.moler_connection_for_single_thread_runner import (
        MolerConnectionForSingleThreadRunner,
    )

    moler_conn = MolerConnectionForSingleThreadRunner(
        encoder=lambda data: data.encode("utf-8"),
        decoder=lambda data: data.decode("utf-8"),
        name="buffer",
    )
    ext_io_in_memory = RemoteConnection(
        moler_connection=moler_conn, echo=False
    )  # we don't want echo on connection
    configure_device_logger(moler_conn.name)
    moler_conn.how2send = ext_io_in_memory.send
    return ext_io_in_memory


def _get_all_states_from_device(device):
    states = copy_list(device.states)
    states.remove("NOT_CONNECTED")
    assert "NOT_CONNECTED" not in states
    states_to_skip = "NOT_CONNECTED"

    for attr_name in dir(device):
        attr = getattr(device, attr_name)
        if type(attr) is str and not attr_name.startswith("_") and attr_name not in dir(TextualDevice):
            if attr not in states and attr not in states_to_skip:
                states.append(attr)

    if "PROXY_PC" in states and hasattr(device, "_use_proxy_pc") and not getattr(device, "_use_proxy_pc"):
        states.remove("PROXY_PC")
    assert "NOT_CONNECTED" not in states
    return states
