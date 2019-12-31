__author__ = 'Marcin Szlapa'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.szlapa@nokia.com'

import pytest

from moler.util.devices_SM import iterate_over_device_states, get_device


def test_scpi_device(device_connection, scpi_output):
    scpi = get_device(name="SCPI", connection=device_connection, device_output=scpi_output,
                      test_file_path=__file__)

    iterate_over_device_states(device=scpi)


def test_scpi_proxy_pc_device(device_connection, scpi_proxy_pc_output):
    scpi_proxy_pc = get_device(name="SCPI_PROXY_PC", connection=device_connection,
                               device_output=scpi_proxy_pc_output, test_file_path=__file__)

    iterate_over_device_states(device=scpi_proxy_pc)


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
