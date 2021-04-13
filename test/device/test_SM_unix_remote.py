__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2021, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import pytest
import time
from moler.util.devices_SM import iterate_over_device_states, get_device
from moler.exceptions import MolerException
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
    with pytest.raises(MolerException) as exception:
        iterate_over_device_states(device=unix_remote_proxy_pc)
    assert "More than 1 prompt match the same line" in str(exception.value)


def test_unix_remote_proxy_pc_device_goto_state_bg(device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc = get_device(name="UNIX_REMOTE_PROXY_PC", connection=device_connection,
                                      device_output=unix_remote_proxy_pc_output, test_file_path=__file__)

    dst_state = "UNIX_REMOTE_ROOT"
    src_state = "UNIX_LOCAL"
    unix_remote_proxy_pc.goto_state(state=src_state)
    assert unix_remote_proxy_pc.current_state == src_state
    unix_remote_proxy_pc.goto_state_bg(state=dst_state)
    assert unix_remote_proxy_pc.current_state != dst_state
    start_time = time.time()
    while dst_state != unix_remote_proxy_pc.current_state:
        MolerTest.sleep(0.1)
        if (time.time() - start_time) > 10:
            break
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
