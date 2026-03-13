__author__ = 'Marcin Szlapa'
__copyright__ = 'Copyright (C) 2019-2026, Nokia'
__email__ = 'marcin.szlapa@nokia.com, marcin.usielski@nokia.com'

import pytest

from moler.util.devices_SM import iterate_over_device_states, DeviceCM


def test_unix_local_device(device_connection, unix_local_output):

    with DeviceCM(name="UNIX_LOCAL", connection=device_connection, device_output=unix_local_output,
                   test_file_path=__file__) as unix_local:
        iterate_over_device_states(device=unix_local)


@pytest.fixture
def unix_local_output():
    output = {
        "UNIX_LOCAL": {
            'su': 'local_root_prompt'
        },
        "UNIX_LOCAL_ROOT": {
            'exit': 'moler_bash#'
        },
    }

    return output
