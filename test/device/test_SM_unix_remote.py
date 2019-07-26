__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'michal.ernst@nokia.com'

import pytest

from moler.util.devices_SM import iterate_over_device_states, get_device


def test_unix_remote_device(device_connection, unix_remote_output):
    unix_remote = get_device(name="UNIX_REMOTE", connection=device_connection, device_output=unix_remote_output,
                             test_file_path=__file__)

    iterate_over_device_states(device=unix_remote)


def test_unix_remote_proxy_pc_device(device_connection, unix_remote_proxy_pc_output):
    unix_remote_proxy_pc = get_device(name="UNIX_REMOTE_PROXY_PC", connection=device_connection,
                                      device_output=unix_remote_proxy_pc_output, test_file_path=__file__)

    iterate_over_device_states(device=unix_remote_proxy_pc)


@pytest.fixture
def unix_remote_output():
    output = {
        "UNIX_LOCAL": {
            'TERM=xterm-mono ssh -l remote_login remote_host': 'remote#',
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
            'TERM=xterm-mono ssh -l proxy_pc_login proxy_pc_host': 'proxy_pc#',
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
            'TERM=xterm-mono ssh -l remote_login remote_host': 'remote#',
            'exit': 'moler_bash#'
        },
        "UNIX_REMOTE_ROOT": {
            'exit': 'remote#',
        },
    }

    return output
