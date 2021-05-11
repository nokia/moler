__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2021, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import pytest
import time
from moler.util.devices_SM import iterate_over_device_states, get_device, get_cloned_device, get_memory_device_connection
from moler.exceptions import MolerException, DeviceChangeStateFailure
from moler.helpers import copy_dict
from moler.util.moler_test import MolerTest


def test_unix_remote_device(device_connection, unix_remote_output):
    unix_remote = get_device(name="UNIX_REMOTE", connection=device_connection, device_output=unix_remote_output,
                             test_file_path=__file__)
    iterate_over_device_states(device=unix_remote)
    assert None is not unix_remote._cmdnames_available_in_state['UNIX_LOCAL_ROOT']


def test_unix_remote_proxy_pc_device(device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc = get_device(name="UNIX_REMOTE_PROXY_PC", connection=device_connection,
                                      device_output=unix_remote_proxy_pc_output, test_file_path=__file__)

    iterate_over_device_states(device=unix_remote_proxy_pc)
    assert None is not unix_remote_proxy_pc._cmdnames_available_in_state['UNIX_LOCAL_ROOT']


def test_unix_remote_proxy_pc_device_multiple_prompts(device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc_changed_output = copy_dict(unix_remote_proxy_pc_output, deep_copy=True)
    combined_line = "moler_bash#"
    for src_state in unix_remote_proxy_pc_output.keys():
        for cmd_string in unix_remote_proxy_pc_output[src_state].keys():
            combined_line = "{} {}".format(combined_line, unix_remote_proxy_pc_output[src_state][cmd_string])
    for src_state in unix_remote_proxy_pc_changed_output.keys():
        for cmd_string in unix_remote_proxy_pc_changed_output[src_state].keys():
            unix_remote_proxy_pc_changed_output[src_state][cmd_string] = combined_line

    unix_remote_proxy_pc = get_device(name="UNIX_REMOTE_PROXY_PC", connection=device_connection,
                                      device_output=unix_remote_proxy_pc_changed_output,
                                      test_file_path=__file__)
    assert unix_remote_proxy_pc._check_all_prompts_on_line is True
    assert unix_remote_proxy_pc._prompts_event.check_against_all_prompts is True

    with pytest.raises(MolerException) as exception:
        iterate_over_device_states(device=unix_remote_proxy_pc, max_no_of_threads=0)
    assert "More than 1 prompt match the same line" in str(exception.value)


def test_unix_remote_proxy_pc_device_goto_state_bg(device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc = get_device(name="UNIX_REMOTE_PROXY_PC", connection=device_connection,
                                      device_output=unix_remote_proxy_pc_output, test_file_path=__file__)
    unix_remote_proxy_pc._goto_state_in_production_mode = True
    dst_state = "UNIX_REMOTE_ROOT"
    src_state = "UNIX_LOCAL"
    unix_remote_proxy_pc.goto_state(state=src_state)
    assert unix_remote_proxy_pc.current_state == src_state
    start_time = time.time()
    unix_remote_proxy_pc.goto_state_bg(state=dst_state)
    assert unix_remote_proxy_pc.current_state != dst_state
    while dst_state != unix_remote_proxy_pc.current_state and (time.time() - start_time) < 10:
        MolerTest.sleep(0.01)
    execution_time_bg = time.time() - start_time
    assert unix_remote_proxy_pc.current_state == dst_state

    unix_remote_proxy_pc.goto_state(state=src_state)
    assert unix_remote_proxy_pc.current_state == src_state
    start_time = time.time()
    unix_remote_proxy_pc.goto_state(state=dst_state)
    execution_time_fg = time.time() - start_time
    assert unix_remote_proxy_pc.current_state == dst_state
    time_diff = abs(execution_time_bg - execution_time_fg)
    assert time_diff < min(execution_time_fg, execution_time_bg) / 2


def test_unix_remote_proxy_pc_device_goto_state_bg_and_goto(device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc = get_device(name="UNIX_REMOTE_PROXY_PC", connection=device_connection,
                                      device_output=unix_remote_proxy_pc_output, test_file_path=__file__)
    unix_remote_proxy_pc._goto_state_in_production_mode = True

    dst_state = "UNIX_REMOTE_ROOT"
    src_state = "UNIX_LOCAL"
    unix_remote_proxy_pc.goto_state(state=src_state)
    assert unix_remote_proxy_pc.current_state == src_state
    unix_remote_proxy_pc.goto_state_bg(state=dst_state)
    assert unix_remote_proxy_pc.current_state != dst_state
    unix_remote_proxy_pc.goto_state(state=dst_state)
    assert unix_remote_proxy_pc.current_state == dst_state


def test_unix_remote_proxy_pc_device_goto_state_bg_await(device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc = get_device(name="UNIX_REMOTE_PROXY_PC", connection=device_connection,
                                      device_output=unix_remote_proxy_pc_output, test_file_path=__file__)
    unix_remote_proxy_pc._goto_state_in_production_mode = True
    dst_state = "UNIX_REMOTE_ROOT"
    src_state = "UNIX_LOCAL"
    unix_remote_proxy_pc.goto_state(state=src_state)
    assert unix_remote_proxy_pc.current_state == src_state
    unix_remote_proxy_pc.goto_state_bg(state=dst_state)
    assert unix_remote_proxy_pc.current_state != dst_state
    unix_remote_proxy_pc.await_goto_state()
    assert unix_remote_proxy_pc.current_state == dst_state


def test_unix_remote_proxy_pc_device_goto_state_bg_await_excption(device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc = get_device(name="UNIX_REMOTE_PROXY_PC", connection=device_connection,
                                      device_output=unix_remote_proxy_pc_output, test_file_path=__file__)
    unix_remote_proxy_pc._goto_state_in_production_mode = True
    dst_state = "UNIX_REMOTE_ROOT"
    src_state = "UNIX_LOCAL"
    unix_remote_proxy_pc.goto_state(state=src_state)
    assert unix_remote_proxy_pc.current_state == src_state
    unix_remote_proxy_pc.goto_state_bg(state=dst_state)
    assert unix_remote_proxy_pc.current_state != dst_state
    with pytest.raises(DeviceChangeStateFailure) as de:
        unix_remote_proxy_pc.await_goto_state(timeout=0.001)
    assert 'seconds there are still states to go' in str(de.value)
    unix_remote_proxy_pc.await_goto_state()
    assert unix_remote_proxy_pc.current_state == dst_state


@pytest.fixture
def unix_remote_output():
    output = {
        "UNIX_LOCAL": {
            'TERM=xterm-mono ssh -l remote_login -o ServerAliveInterval=7 -o ServerAliveCountMax=2 remote_host': 'remote#',
            'su': 'local_root_prompt'
        },
        "UNIX_LOCAL_ROOT": {
            'exit': 'moler_bash#'
        },
        "UNIX_REMOTE": {
            'exit': 'moler_bash#',
            'su': 'remote_root_prompt'
        },
        "UNIX_REMOTE_ROOT": {
            'exit': 'remote#',
        },
    }

    return output


@pytest.fixture
def unix_remote_proxy_pc_output():
    output = {
        "UNIX_LOCAL": {
            'TERM=xterm-mono ssh -l proxy_pc_login -o ServerAliveInterval=7 -o ServerAliveCountMax=2 proxy_pc_host': 'proxy_pc#',
            'su': 'local_root_prompt'
        },
        "UNIX_LOCAL_ROOT": {
            'exit': 'moler_bash#'
        },
        "UNIX_REMOTE": {
            'exit': 'proxy_pc#',
            'su': 'remote_root_prompt'
        },
        "PROXY_PC": {
            'TERM=xterm-mono ssh -l remote_login -o ServerAliveInterval=7 -o ServerAliveCountMax=2 remote_host': 'remote#',
            'exit': 'moler_bash#'
        },
        "UNIX_REMOTE_ROOT": {
            'exit': 'remote#',
        },
    }

    return output
