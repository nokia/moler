# -*- coding: utf-8 -*-
"""
Testing of ip route command.
"""
__author__ = 'Yang Snackwell'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'snackwell.yang@nokia-sbell.com'


def test_calling_iproute_returns_result_parsed_from_command_output(buffer_connection):
    from moler.cmd.unix.ip_route import Ip_route
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    iproute_cmd = Ip_route(connection=buffer_connection.moler_connection)
    result = iproute_cmd()
    assert result == expected_result

def test_calling_iproute_get_default_returns_result_parsed_from_command_output(buffer_connection):
    from moler.cmd.unix.ip_route import Ip_route
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    iproute_cmd = Ip_route(connection=buffer_connection.moler_connection)
    iproute_cmd()
    result = iproute_cmd.get_default_route()
    expected_default_route="10.83.207.254"
    assert result == expected_default_route

def test_iproute_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.ip_route import Ip_route
    iproute_cmd = Ip_route(buffer_connection, is_ipv6=True)
    assert "ip -6 route" == iproute_cmd.command_string


def command_output_and_expected_result():
    data = """
 FZM-TDD-248:/l # ip route
 default via 10.83.207.254 dev eth0  proto dhcp
 10.0.0.0/24 dev eth3  proto kernel  scope link  src 10.0.0.2
 10.1.52.248 via 10.0.0.248 dev eth3
 10.83.200.0/21 dev eth0  proto kernel  scope link  src 10.83.204.18
 10.83.224.0/23 via 10.89.5.126 dev eth2
 10.89.5.0/25 dev eth2  proto kernel  scope link  src 10.89.5.52
 10.254.0.0/16 via 10.89.5.126 dev eth2
 41.1.0.0/20 dev tunPGW  proto kernel  scope link  src 41.1.1.254
 192.168.255.0/24 dev eth1  proto kernel  scope link  src 192.168.255.126
 FZM-TDD-248:/l # """
    result = {
    'ADDRESS': {'10.0.0.0/24': {'ADDRESS': '10.0.0.0/24',
                            'DEV': 'eth3',
                            'PROTO': 'kernel',
                            'SCOPE': 'link',
                            'SRC': '10.0.0.2'},
            '10.83.200.0/21': {'ADDRESS': '10.83.200.0/21',
                               'DEV': 'eth0',
                               'PROTO': 'kernel',
                               'SCOPE': 'link',
                               'SRC': '10.83.204.18'},
            '10.89.5.0/25': {'ADDRESS': '10.89.5.0/25',
                             'DEV': 'eth2',
                             'PROTO': 'kernel',
                             'SCOPE': 'link',
                             'SRC': '10.89.5.52'},
            '192.168.255.0/24': {'ADDRESS': '192.168.255.0/24',
                                 'DEV': 'eth1',
                                 'PROTO': 'kernel',
                                 'SCOPE': 'link',
                                 'SRC': '192.168.255.126'},
            '41.1.0.0/20': {'ADDRESS': '41.1.0.0/20',
                            'DEV': 'tunPGW',
                            'PROTO': 'kernel',
                            'SCOPE': 'link',
                            'SRC': '41.1.1.254'}},
'ALL': [{'ADDRESS': 'default', 'DEV': 'eth0', 'VIA': '10.83.207.254'},
        {'ADDRESS': '10.0.0.0/24',
         'DEV': 'eth3',
         'PROTO': 'kernel',
         'SCOPE': 'link',
         'SRC': '10.0.0.2'},
        {'ADDRESS': '10.1.52.248', 'DEV': 'eth3', 'VIA': '10.0.0.248'},
        {'ADDRESS': '10.83.200.0/21',
         'DEV': 'eth0',
         'PROTO': 'kernel',
         'SCOPE': 'link',
         'SRC': '10.83.204.18'},
        {'ADDRESS': '10.83.224.0/23', 'DEV': 'eth2', 'VIA': '10.89.5.126'},
        {'ADDRESS': '10.89.5.0/25',
         'DEV': 'eth2',
         'PROTO': 'kernel',
         'SCOPE': 'link',
         'SRC': '10.89.5.52'},
        {'ADDRESS': '10.254.0.0/16', 'DEV': 'eth2', 'VIA': '10.89.5.126'},
        {'ADDRESS': '41.1.0.0/20',
         'DEV': 'tunPGW',
         'PROTO': 'kernel',
         'SCOPE': 'link',
         'SRC': '41.1.1.254'},
        {'ADDRESS': '192.168.255.0/24',
         'DEV': 'eth1',
         'PROTO': 'kernel',
         'SCOPE': 'link',
         'SRC': '192.168.255.126'}],
'VIA': {'10.1.52.248': {'ADDRESS': '10.1.52.248',
                        'DEV': 'eth3',
                        'VIA': '10.0.0.248'},
        '10.254.0.0/16': {'ADDRESS': '10.254.0.0/16',
                          'DEV': 'eth2',
                          'VIA': '10.89.5.126'},
        '10.83.224.0/23': {'ADDRESS': '10.83.224.0/23',
                           'DEV': 'eth2',
                           'VIA': '10.89.5.126'},
        'default': {'ADDRESS': 'default',
                    'DEV': 'eth0',
                    'VIA': '10.83.207.254'}}}

    return data, result
