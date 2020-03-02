__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import pytest

from moler.util.devices_SM import iterate_over_device_states, get_device


def test_at_remote_device(device_connection, at_remote_output):
    at_remote = get_device(name="AT_REMOTE", connection=device_connection, device_output=at_remote_output,
                           test_file_path=__file__)

    iterate_over_device_states(device=at_remote)


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
