__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest

from moler.util.devices_SM import iterate_over_device_states, get_device


def test_pdu_device(device_connection, pdu_output):
    pdu = get_device(name="PDU", connection=device_connection, device_output=pdu_output,
                     test_file_path=__file__)

    iterate_over_device_states(device=pdu)


def test_pdu_proxy_pc_device(device_connection, pdu_proxy_pc_output):
    pdu = get_device(name="PDU_PROXY_PC", connection=device_connection,
                     device_output=pdu_proxy_pc_output, test_file_path=__file__)

    iterate_over_device_states(device=pdu)


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
