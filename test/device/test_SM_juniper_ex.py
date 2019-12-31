__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'michal.ernst@nokia.com'

import pytest
from moler.util.devices_SM import iterate_over_device_states, get_device


def test_juniper_ex_device(device_connection, juniper_ex_output):
    juniper_ex = get_device(name="JUNIPER_EX", connection=device_connection, device_output=juniper_ex_output,
                            test_file_path=__file__)
    iterate_over_device_states(device=juniper_ex)


def test_juniper_ex_proxy_pc_device(device_connection, juniper_ex_proxy_pc_output):
    juniper_ex_proxy_pc = get_device(name="JUNIPER_EX_PROXY_PC", connection=device_connection,
                                     device_output=juniper_ex_proxy_pc_output, test_file_path=__file__)
    iterate_over_device_states(device=juniper_ex_proxy_pc)


@pytest.fixture
def juniper_ex_output():
    output = {
        "UNIX_LOCAL": {
            'TERM=xterm-mono ssh -l cli_login -o ServerAliveInterval=7 -o ServerAliveCountMax=2 cli_host': 'admin@switch>',
            'su': 'local_root_prompt'
        },
        "UNIX_LOCAL_ROOT": {
            'exit': 'moler_bash#'
        },
        "CLI": {
            'exit': 'moler_bash#',
            'configure': 'admin@switch#'
        },
        "CONFIGURE": {
            'exit': 'admin@switch>',
        },
    }

    return output


@pytest.fixture
def juniper_ex_proxy_pc_output():
    output = {
        "UNIX_LOCAL": {
            'TERM=xterm-mono ssh -l proxy_pc_login -o ServerAliveInterval=7 -o ServerAliveCountMax=2 proxy_pc_host': 'proxy_pc#',
            'su': 'local_root_prompt'
        },
        "UNIX_LOCAL_ROOT": {
            'exit': 'moler_bash#'
        },
        "PROXY_PC": {
            'TERM=xterm-mono ssh -l cli_login -o ServerAliveInterval=7 -o ServerAliveCountMax=2 cli_host': 'admin@switch>',
            'exit': 'moler_bash#'
        },
        "CLI": {
            'configure': 'admin@switch#',
            'exit': 'proxy_pc#'
        },
        "CONFIGURE": {
            'exit': 'admin@switch>'
        }
    }

    return output
