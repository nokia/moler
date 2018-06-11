# -*- coding: utf-8 -*-
"""
Testing of Nmap command.
"""

__author__ = 'Yeshu Yang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yeshu.yang@nokia-sbell.com'

import pytest
from pytest import raises
from moler.cmd.unix.nmap import Nmap


def test_nmap_returns_proper_command_string(buffer_connection):
    nmap_cmd = Nmap(buffer_connection, ip="192.168.255.3", is_ping=True)
    assert "nmap 192.168.255.3" == nmap_cmd.command_string


def test_calling_nmap_timeout(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_timeout()
    buffer_connection.remote_inject_response([command_output])
    nmap_cmd = Nmap(connection=buffer_connection.moler_connection, ip="192.168.255.3")
    from moler.exceptions import CommandTimeout
    with raises(CommandTimeout) as exception:
        nmap_cmd(timeout=0.5)
    assert exception is not None

# --------------------------- resources


@pytest.fixture
def command_output_and_expected_result_timeout():
    data = """"root@cp19-nj:/home/ute# nmap -d1 -p- -S 192.168.255.126 192.168.255.4 -PN

Starting Nmap 6.00 ( http://nmap.org ) at 2018-05-25 08:40 CST
--------------- Timing report ---------------
  hostgroups: min 1, max 100000
  rtt-timeouts: init 1000, min 100, max 10000
  max-scan-delay: TCP 1000, UDP 1000, SCTP 1000
  parallelism: min 0, max 0
  max-retries: 10, host-timeout: 0
  min-rate: 0, max-rate: 0
---------------------------------------------
Initiating ARP Ping Scan at 08:40
Scanning 192.168.255.4 [1 port]
Packet capture filter (device eth1): arp and arp[18:4] = 0xFE365EB1 and arp[22:2] = 0x1AE6
Completed ARP Ping Scan at 08:40, 0.43s elapsed (1 total hosts)
Overall sending rates: 4.61 packets / s, 193.61 bytes / s.
mass_rdns: Using DNS server 135.251.124.100
mass_rdns: Using DNS server 135.251.38.218
Nmap scan report for 192.168.255.4 [host down, received no-response]
Read from /usr/bin/../share/nmap: nmap-payloads nmap-services.
Nmap done: 1 IP address (0 hosts up) scanned in 0.54 seconds
           Raw packets sent: 2 (56B) | Rcvd: 0 (0B) """
    result = {}
    return data, result
