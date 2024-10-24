__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020-2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest

from moler.util.devices_SM import iterate_over_device_states, get_device


pdus = ["PDU", "PDU3"]
pdus_proxy = ["PDU_PROXY_PC", "PDU_PROXY_PC3"]


@pytest.mark.parametrize("device_name", pdus)
def test_pdu_device(device_name, device_connection, pdu_output):
    pdu = get_device(name=device_name, connection=device_connection, device_output=pdu_output,
                     test_file_path=__file__)

    iterate_over_device_states(device=pdu)


@pytest.mark.parametrize("device_name", pdus_proxy)
def test_pdu_proxy_pc_device(device_name, device_connection, pdu_proxy_pc_output):
    pdu = get_device(name=device_name, connection=device_connection,
                     device_output=pdu_proxy_pc_output, test_file_path=__file__)

    iterate_over_device_states(device=pdu)


@pytest.mark.parametrize("devices", [pdus, pdus_proxy])
def test_unix_sm_identity(devices):
    from moler.device import DeviceFactory
    dev0 = DeviceFactory.get_device(name=devices[0])
    dev1 = DeviceFactory.get_device(name=devices[1])

    assert dev0._stored_transitions == dev1._stored_transitions
    assert dev0._state_hops == dev1._state_hops
    assert dev0._state_prompts == dev1._state_prompts
    assert dev0._configurations == dev1._configurations
    assert dev0._newline_chars == dev1._newline_chars


@pytest.fixture
def pdu_output():
    output = {
        "UNIX_LOCAL": {
            'TERM=xterm-mono telnet 10.0.0.1': '>',
            'su': 'local_root_prompt'
        },
        "UNIX_LOCAL_ROOT": {
            'exit': 'moler_bash#'
        },
        "PDU": {
            '\x1d': 'telnet>',
            'q\r': 'moler_bash#',
        },
    }

    return output


@pytest.fixture
def pdu_proxy_pc_output():
    output = {
        "UNIX_LOCAL": {
            'TERM=xterm-mono ssh -l proxy_pc_login -o ServerAliveInterval=7 -o ServerAliveCountMax=2 proxy_pc_host': 'proxy_pc#',
            'su': 'local_root_prompt'
        },
        "PROXY_PC": {
            'TERM=xterm-mono telnet 10.0.0.1': '>',
            'exit': 'moler_bash#'
        },
        "UNIX_LOCAL_ROOT": {
            'exit': 'moler_bash#'
        },
        "PDU": {
            '\x1d': 'telnet>',
            'q\r': 'proxy_pc#',
        },
    }

    return output
