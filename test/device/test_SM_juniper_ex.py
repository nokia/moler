__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2024, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import pytest
from moler.device import DeviceFactory
from moler.util.devices_SM import iterate_over_device_states, get_device


junipers = ['JUNIPER_EX', 'JUNIPER_EX3']
junipers_proxy = ['JUNIPER_EX_PROXY_PC', 'JUNIPER_EX_PROXY_PC3']

@pytest.mark.parametrize("device_name", junipers)
def test_juniper_ex_device(device_name, device_connection, juniper_ex_output):
    juniper_ex = get_device(name=device_name, connection=device_connection, device_output=juniper_ex_output,
                            test_file_path=__file__)
    iterate_over_device_states(device=juniper_ex)


@pytest.mark.parametrize("device_name", junipers_proxy)
def test_juniper_ex_proxy_pc_device(device_name, device_connection, juniper_ex_proxy_pc_output):
    juniper_ex_proxy_pc = get_device(name=device_name, connection=device_connection,
                                     device_output=juniper_ex_proxy_pc_output, test_file_path=__file__)
    iterate_over_device_states(device=juniper_ex_proxy_pc)


@pytest.mark.parametrize("devices", [junipers_proxy, junipers])
def test_unix_sm_identity(devices):
    dev0 = DeviceFactory.get_device(name=devices[0])
    dev1 = DeviceFactory.get_device(name=devices[1])

    assert dev0._stored_transitions == dev1._stored_transitions
    assert dev0._state_hops == dev1._state_hops
    assert dev0._state_prompts == dev1._state_prompts
    assert dev0._configurations == dev1._configurations
    assert dev0._newline_chars == dev1._newline_chars


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
