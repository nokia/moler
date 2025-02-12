__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2020-2025, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'

import pytest

from moler.util.devices_SM import iterate_over_device_states, get_device, moler_check_sm_identity

at_remotes = ["AT_REMOTE", "AT_REMOTE3"]
at_remotes_proxy_pc = ["AT_REMOTE_PROXY_PC", "AT_REMOTE_PROXY_PC3"]


@pytest.mark.parametrize("device_name", at_remotes)
def test_at_remote_device(device_name, device_connection, at_remote_output):
    at_remote = get_device(name=device_name, connection=device_connection, device_output=at_remote_output,
                           test_file_path=__file__)

    iterate_over_device_states(device=at_remote)


@pytest.mark.parametrize("device_name", at_remotes_proxy_pc)
def test_at_remote_device_proxy_pc(device_name, device_connection, at_remote_output_proxy_pc):
    at_remote = get_device(name=device_name, connection=device_connection, device_output=at_remote_output_proxy_pc,
                           test_file_path=__file__)

    iterate_over_device_states(device=at_remote)


@pytest.mark.parametrize("devices", [at_remotes_proxy_pc, at_remotes])
def test_unix_sm_identity(devices, device_connection, at_remote_output):
    dev0 = get_device(name=devices[0], connection=device_connection, device_output=at_remote_output,
                      test_file_path=__file__)
    dev1 = get_device(name=devices[1], connection=device_connection, device_output=at_remote_output,
                      test_file_path=__file__)
    moler_check_sm_identity([dev0, dev1])

@pytest.fixture
def at_remote_output():
    plink_cmd_string = 'plink -serial COM5 |& awk \'BEGIN {print "COM5> port READY"} {print} END {print "^C"}\''
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
            'su': 'remote_root_prompt',
            plink_cmd_string: 'COM5>'
        },
        "AT_REMOTE": {
            '\x03': '^C\nremote#',
        },
        "UNIX_REMOTE_ROOT": {
            'exit': 'remote#',
        },
    }

    return output


@pytest.fixture
def at_remote_output_proxy_pc():
    plink_cmd_string = 'plink -serial COM5 |& awk \'BEGIN {print "COM5> port READY"} {print} END {print "^C"}\''
    output = {
        "UNIX_LOCAL": {
            'TERM=xterm-mono ssh -l proxy_pc_login -o ServerAliveInterval=7 -o ServerAliveCountMax=2 proxy_pc_host': 'proxy_pc#',
            'su': 'local_root_prompt'
        },
        "PROXY_PC": {
            'TERM=xterm-mono ssh -l remote_login -o ServerAliveInterval=7 -o ServerAliveCountMax=2 remote_host': 'remote#',
            'exit': 'moler_bash#',
        },
        "UNIX_LOCAL_ROOT": {
            'exit': 'moler_bash#'
        },
        "UNIX_REMOTE": {
            'exit': 'proxy_pc#',
            'su': 'remote_root_prompt',
            plink_cmd_string: 'COM5>'
        },
        "AT_REMOTE": {
            '\x03': '^C\nremote#',
        },
        "UNIX_REMOTE_ROOT": {
            'exit': 'remote#',
        },
    }

    return output
