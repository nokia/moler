__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2024, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import pytest
import time
import os
import platform
from moler.util.devices_SM import iterate_over_device_states, get_device
from moler.exceptions import MolerException, DeviceChangeStateFailure
from moler.helpers import copy_dict
from moler.util.moler_test import MolerTest
from moler.device import DeviceFactory
from moler.config import load_config
from moler.exceptions import DeviceFailure


unix_remotes=['UNIX_REMOTE', 'UNIX_REMOTE3']
unix_remotes_proxy_pc=['UNIX_REMOTE_PROXY_PC', 'UNIX_REMOTE3_PROXY_PC']
unix_remotes_real_io = ['UNIX_REMOTE_REAL_IO', 'UNIX_REMOTE3_REAL_IO']


@pytest.mark.parametrize("device_name", unix_remotes)
def test_unix_remote_device(device_name, device_connection, unix_remote_output):
    unix_remote = get_device(name=device_name, connection=device_connection, device_output=unix_remote_output,
                             test_file_path=__file__)
    iterate_over_device_states(device=unix_remote)
    assert None is not unix_remote._cmdnames_available_in_state['UNIX_LOCAL_ROOT']


@pytest.mark.parametrize("device_name", unix_remotes_proxy_pc)
def test_unix_remote_proxy_pc_device(device_name, device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc = get_device(name=device_name, connection=device_connection,
                                      device_output=unix_remote_proxy_pc_output, test_file_path=__file__)

    iterate_over_device_states(device=unix_remote_proxy_pc)
    assert None is not unix_remote_proxy_pc._cmdnames_available_in_state['UNIX_LOCAL_ROOT']


@pytest.mark.parametrize("device_name", unix_remotes_proxy_pc)
def test_unix_remote_proxy_pc_device_multiple_prompts(device_name, device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc_changed_output = copy_dict(unix_remote_proxy_pc_output, deep_copy=True)
    combined_line = "moler_bash#"
    for src_state in unix_remote_proxy_pc_output.keys():
        for cmd_string in unix_remote_proxy_pc_output[src_state].keys():
            combined_line = f"{combined_line} {unix_remote_proxy_pc_output[src_state][cmd_string]}"
    for src_state in unix_remote_proxy_pc_changed_output.keys():
        for cmd_string in unix_remote_proxy_pc_changed_output[src_state].keys():
            unix_remote_proxy_pc_changed_output[src_state][cmd_string] = combined_line

    unix_remote_proxy_pc = get_device(name=device_name, connection=device_connection,
                                      device_output=unix_remote_proxy_pc_changed_output,
                                      test_file_path=__file__)
    assert unix_remote_proxy_pc._check_all_prompts_on_line is True
    assert unix_remote_proxy_pc._prompts_event.check_against_all_prompts is True

    with pytest.raises(MolerException) as exception:
        iterate_over_device_states(device=unix_remote_proxy_pc, max_no_of_threads=0)
    assert "More than 1 prompt match the same line" in str(exception.value)


pytest.mark.skipif('Linux' != platform.system(), reason="Skip for no Linux system.")
@pytest.mark.parametrize("device_name", unix_remotes_proxy_pc)
def test_unix_remote_proxy_pc_device_goto_state_bg(device_name, device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc = get_device(name=device_name, connection=device_connection,
                                      device_output=unix_remote_proxy_pc_output, test_file_path=__file__)
    unix_remote_proxy_pc._goto_state_in_production_mode = True
    dst_state = "UNIX_REMOTE_ROOT"
    src_state = "UNIX_LOCAL"

    unix_remote_proxy_pc.goto_state(state=src_state, sleep_after_changed_state=0)
    assert unix_remote_proxy_pc.current_state == src_state
    start_time = time.monotonic()
    unix_remote_proxy_pc.goto_state_bg(state=dst_state)
    assert unix_remote_proxy_pc.current_state != dst_state
    while dst_state != unix_remote_proxy_pc.current_state and (time.monotonic() - start_time) < 10:
        MolerTest.sleep(0.01)
    execution_time_bg = time.monotonic() - start_time
    assert unix_remote_proxy_pc.current_state == dst_state

    unix_remote_proxy_pc.goto_state(state=src_state, sleep_after_changed_state=0)
    assert unix_remote_proxy_pc.current_state == src_state
    start_time = time.monotonic()
    unix_remote_proxy_pc.goto_state(state=dst_state, sleep_after_changed_state=0)
    execution_time_fg = time.monotonic() - start_time
    assert unix_remote_proxy_pc.current_state == dst_state
    time_diff = abs(execution_time_bg - execution_time_fg)
    assert time_diff < max(execution_time_fg, execution_time_bg)


@pytest.mark.parametrize("device_name", unix_remotes_proxy_pc)
def test_unix_remote_proxy_pc_device_goto_state_bg_and_goto(device_name, device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc = get_device(name=device_name, connection=device_connection,
                                      device_output=unix_remote_proxy_pc_output, test_file_path=__file__)
    unix_remote_proxy_pc._goto_state_in_production_mode = True

    dst_state = "UNIX_REMOTE_ROOT"
    src_state = "UNIX_LOCAL"
    unix_remote_proxy_pc.goto_state(state=src_state, sleep_after_changed_state=0)
    assert unix_remote_proxy_pc.current_state == src_state
    unix_remote_proxy_pc.goto_state_bg(state=dst_state)
    assert unix_remote_proxy_pc.current_state != dst_state
    unix_remote_proxy_pc.goto_state(state=dst_state, sleep_after_changed_state=0)
    assert unix_remote_proxy_pc.current_state == dst_state


@pytest.mark.parametrize("device_name", unix_remotes_proxy_pc)
def test_unix_remote_proxy_pc_device_goto_state_bg_await(device_name, device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc = get_device(name=device_name, connection=device_connection,
                                      device_output=unix_remote_proxy_pc_output, test_file_path=__file__)
    unix_remote_proxy_pc._goto_state_in_production_mode = True
    dst_state = "UNIX_REMOTE_ROOT"
    src_state = "UNIX_LOCAL"
    unix_remote_proxy_pc.goto_state(state=src_state, sleep_after_changed_state=0)
    assert unix_remote_proxy_pc.current_state == src_state
    unix_remote_proxy_pc.goto_state_bg(state=dst_state)
    assert unix_remote_proxy_pc.current_state != dst_state
    unix_remote_proxy_pc.await_goto_state()
    assert unix_remote_proxy_pc.current_state == dst_state


@pytest.mark.parametrize("device_name", unix_remotes_proxy_pc)
def test_unix_remote_proxy_pc_device_goto_state_bg_await_exception(device_name, device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc = get_device(name=device_name, connection=device_connection,
                                      device_output=unix_remote_proxy_pc_output, test_file_path=__file__)
    unix_remote_proxy_pc._goto_state_in_production_mode = True
    dst_state = "UNIX_REMOTE_ROOT"
    src_state = "UNIX_LOCAL"
    unix_remote_proxy_pc.goto_state(state=src_state, sleep_after_changed_state=0)
    assert unix_remote_proxy_pc.current_state == src_state
    unix_remote_proxy_pc.goto_state_bg(state=dst_state)
    assert unix_remote_proxy_pc.current_state != dst_state
    with pytest.raises(DeviceChangeStateFailure) as de:
        unix_remote_proxy_pc.await_goto_state(timeout=0.001)
    assert 'seconds there are still states to go' in str(de.value)
    unix_remote_proxy_pc.await_goto_state()
    assert unix_remote_proxy_pc.current_state == dst_state


@pytest.mark.parametrize("device_name", unix_remotes_real_io)
def test_unix_remote_device_not_connected(device_name):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    load_config(os.path.join(dir_path, os.pardir, os.pardir, 'test', 'resources', 'device_config.yml'))
    unix_remote = DeviceFactory.get_device(name=device_name, initial_state="UNIX_LOCAL")
    unix_remote.goto_state("UNIX_LOCAL", sleep_after_changed_state=0)
    cmd_whoami = unix_remote.get_cmd(cmd_name="whoami")
    ret1 = cmd_whoami()
    execution = 0
    while execution < 5:
        unix_remote.goto_state("NOT_CONNECTED", sleep_after_changed_state=0)
        with pytest.raises(DeviceFailure) as ex:
            cmd_whoami = unix_remote.get_cmd(cmd_name="whoami")
            cmd_whoami()
        assert "cmd is unknown for state 'NOT_CONNECTED'" in str(ex)
        assert unix_remote.io_connection._terminal is None
        assert unix_remote.io_connection.moler_connection.is_open() is False
        unix_remote.goto_state("UNIX_LOCAL", sleep_after_changed_state=0)
        assert unix_remote.io_connection._terminal is not None
        assert unix_remote.io_connection.moler_connection.is_open() is True
        cmd_whoami = unix_remote.get_cmd(cmd_name="whoami")
        ret2 = cmd_whoami()
        assert ret1 == ret2
        execution += 1


@pytest.mark.parametrize("devices", [unix_remotes, unix_remotes_proxy_pc, unix_remotes_real_io])
def test_unix_sm_identity(devices):
    dev0 = DeviceFactory.get_device(name=devices[0])
    dev1 = DeviceFactory.get_device(name=devices[1])

    assert dev0._stored_transitions == dev1._stored_transitions
    assert dev0._state_hops == dev1._state_hops
    assert dev0._state_prompts == dev1._state_prompts
    assert dev0._configurations == dev1._configurations
    assert dev0._newline_chars == dev1._newline_chars


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
