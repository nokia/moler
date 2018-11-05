# -*- coding: utf-8 -*-
"""
Testing of Df command.
"""

__author__ = 'Yeshu Yang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yeshu.yang@nokia.com'

import pytest

def test_calling_df_returns_result(buffer_connection, command_output_and_expected_result):
    from moler.cmd.unix.df import Df
    command_output, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response([command_output])
    df_cmd = Df(connection=buffer_connection.moler_connection)
    result = df_cmd()
    assert result == expected_result

# --------------------------- resources


@pytest.fixture
def command_output_and_expected_result():
    data = """
[root@Pclinux90: /home/runner]# df -BM -T -P
Filesystem    Type 1048576-blocks      Used Available Capacity Mounted on
/dev/sda2     ext3          4039M     1760M     2073M      46% /
udev         tmpfs           999M        1M      999M       1% /dev
/dev/sda3     ext3        144169M   109553M    27293M      81% /home
//175.28.247.174/emssim cifs      433150M     7865M   403282M       2% /home/emssim
//175.28.247.165/vobs cifs      918588M     1299M   916356M       1% /vobs
//175.28.247.165/vob cifs      918588M     1299M   916356M       1% /vob
//175.28.247.165/cc cifs      918588M     1299M   916356M       1% /cc
[root@Pclinux90: /home/runner]#"""

    result = {
        'by_FS': {
            '//175.28.247.165/vobs': {'Avail': '916356', 'Used': '1299', 'Type': 'cifs', 'Size': '918588',
                                      'Filesystem': '//175.28.247.165/vobs', 'Mounted_on': '/vobs', 'Use_percentage': '1'},
            '//175.28.247.165/vob': {'Avail': '916356', 'Used': '1299', 'Type': 'cifs', 'Size': '918588',
                                     'Filesystem': '//175.28.247.165/vob', 'Mounted_on': '/vob', 'Use_percentage': '1'},
            '/dev/sda3': {'Avail': '27293', 'Used': '109553', 'Type': 'ext3', 'Size': '144169',
                          'Filesystem': '/dev/sda3', 'Mounted_on': '/home', 'Use_percentage': '81'},
            '//175.28.247.165/cc': {'Avail': '916356', 'Used': '1299', 'Type': 'cifs', 'Size': '918588',
                                    'Filesystem': '//175.28.247.165/cc', 'Mounted_on': '/cc', 'Use_percentage': '1'},
            '/dev/sda2': {'Avail': '2073', 'Used': '1760', 'Type': 'ext3', 'Size': '4039',
                          'Filesystem': '/dev/sda2', 'Mounted_on': '/', 'Use_percentage': '46'},
            '//175.28.247.174/emssim': {'Avail': '403282', 'Used': '7865', 'Type': 'cifs', 'Size': '433150',
                                        'Filesystem': '//175.28.247.174/emssim', 'Mounted_on': '/home/emssim', 'Use_percentage': '2'},
            'udev': {'Avail': '999', 'Used': '1', 'Type': 'tmpfs', 'Size': '999',
                     'Filesystem': 'udev', 'Mounted_on': '/dev', 'Use_percentage': '1'}
        },
        'by_MOUNTPOINT': {
            '/home/emssim': {'Avail': '403282', 'Used': '7865', 'Type': 'cifs', 'Size': '433150',
                             'Filesystem': '//175.28.247.174/emssim', 'Mounted_on': '/home/emssim', 'Use_percentage': '2'},
            '/': {'Avail': '2073', 'Used': '1760', 'Type': 'ext3', 'Size': '4039',
                  'Filesystem': '/dev/sda2', 'Mounted_on': '/', 'Use_percentage': '46'},
            '/dev': {'Avail': '999', 'Used': '1', 'Type': 'tmpfs', 'Size': '999',
                     'Filesystem': 'udev', 'Mounted_on': '/dev', 'Use_percentage': '1'},
            '/vobs': {'Avail': '916356', 'Used': '1299', 'Type': 'cifs', 'Size': '918588',
                      'Filesystem': '//175.28.247.165/vobs', 'Mounted_on': '/vobs', 'Use_percentage': '1'},
            '/vob': {'Avail': '916356', 'Used': '1299', 'Type': 'cifs', 'Size': '918588',
                     'Filesystem': '//175.28.247.165/vob', 'Mounted_on': '/vob', 'Use_percentage': '1'},
            '/cc': {'Avail': '916356', 'Used': '1299', 'Type': 'cifs', 'Size': '918588',
                    'Filesystem': '//175.28.247.165/cc', 'Mounted_on': '/cc', 'Use_percentage': '1'},
            '/home': {'Avail': '27293', 'Used': '109553', 'Type': 'ext3', 'Size': '144169',
                      'Filesystem': '/dev/sda3', 'Mounted_on': '/home', 'Use_percentage': '81'}
        }
    }
    return data, result
