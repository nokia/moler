__author__ = 'Marcin Szlapa'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.szlapa@nokia.com'

import pytest

from moler.util.devices_SM import iterate_over_device_states, get_device


def test_unix_local_device(device_connection, unix_local_output):
    unix_local = get_device(name="UNIX_LOCAL", connection=device_connection, device_output=unix_local_output,
                            test_file_path=__file__)

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
