__author__ = 'Marcin Szlapa, Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2024, Nokia'
__email__ = 'marcin.szlapa@nokia.com, marcin.usielski@nokia.com'

import pytest

from moler.util.devices_SM import iterate_over_device_states, get_device

scpis = ["SCPI", "SCPI3"]
scpis_proxy = ["SCPI_PROXY_PC", "SCPI_PROXY_PC3"]


@pytest.mark.parametrize("device_name", scpis)
def test_scpi_device(device_name, device_connection, scpi_output):
    scpi = get_device(name=device_name, connection=device_connection, device_output=scpi_output,
                      test_file_path=__file__)

    iterate_over_device_states(device=scpi)


@pytest.mark.parametrize("device_name", scpis_proxy)
def test_scpi_proxy_pc_device(device_name, device_connection, scpi_proxy_pc_output):
    scpi_proxy_pc = get_device(name=device_name, connection=device_connection,
                               device_output=scpi_proxy_pc_output, test_file_path=__file__)

    iterate_over_device_states(device=scpi_proxy_pc)


@pytest.mark.parametrize("devices", [scpis, scpis_proxy])
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
def scpi_output():
    output = {
        "UNIX_LOCAL": {
            'TERM=xterm-mono telnet 10.0.0.1 99999': 'SCPI>',
            'su': 'local_root_prompt'
        },
        "UNIX_LOCAL_ROOT": {
            'exit': 'moler_bash#'
        },
        "SCPI": {
            '\x1d': 'telnet>',
            'q\r': 'moler_bash#',
        },
    }

    return output


@pytest.fixture
def scpi_proxy_pc_output():
    output = {
        "UNIX_LOCAL": {
            'TERM=xterm-mono ssh -l proxy_pc_login -o ServerAliveInterval=7 -o ServerAliveCountMax=2 proxy_pc_host': 'proxy_pc#',
            'su': 'local_root_prompt'
        },
        "PROXY_PC": {
            'TERM=xterm-mono telnet 10.0.0.1 99999': 'SCPI>',
            'exit': 'moler_bash#'
        },
        "UNIX_LOCAL_ROOT": {
            'exit': 'moler_bash#'
        },
        "SCPI": {
            '\x1d': 'telnet>',
            'q\r': 'proxy_pc#',
        },
    }

    return output
