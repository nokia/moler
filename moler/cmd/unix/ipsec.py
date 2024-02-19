# -*- coding: utf-8 -*-
"""
Ipsec command module.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Ipsec(GenericUnixCommand):

    def __init__(self, connection, options, prompt=None, newline_chars=None, runner=None):
        super(Ipsec, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.options = options
        self.ret_required = False

        self.status = None
        self.listening_ip_addr = None
        self.security_associations = None
        self.connections = None
        self.entry_key = None

    def build_command_string(self):
        return f"ipsec {self.options}"

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_status_deamon(line)
                self._parse_listening_ip_addr(line)
                self._parse_security_associations(line)
                self._parse_connections(line)
                self._parse_conn_key_value_key2_value2(line)
                self._parse_conn_key_tunnel_key2_value(line)
                self._parse_conn_key_value(line)
                self._parse_key_value(line)
                self._parse_ip_addr(line)
                self._parse_ike_group_estabilshed_ago_local_ramote_tep(line)
                self._parse_ike_group(line)
                self._parse_child_group(line)
            except ParsingDone:
                pass  # line has been fully parsed by one of above parse-methods
        return super(Ipsec, self).on_new_line(line, is_full_line)

    # Status of IKE charon daemon (strongSwan 5.2.2, Linux 4.4.112-rt127, armv7l):
    _re_status_deamon = re.compile(r"^(?P<STATUS>Status[\w\s]*\w)\s*\((?P<DAEMON>\S+)\s+(?P<DAEMON_VER>\S+),.*\):$")

    def _parse_status_deamon(self, line):
        if self._regex_helper.search_compiled(Ipsec._re_status_deamon, line):
            self.status = self._regex_helper.group('STATUS')
            self.current_ret[self.status] = {}
            self.current_ret[self.status][self._regex_helper.group('DAEMON')] = self._regex_helper.group('DAEMON_VER')
            raise ParsingDone

    # Listening IP addresses:
    _re_listening_ip_addr = re.compile(r"^Listening")

    def _parse_listening_ip_addr(self, line):
        if self._regex_helper.search_compiled(Ipsec._re_listening_ip_addr, line):
            self.listening_ip_addr = True
            self.status = None
            self.current_ret['Listening IP addresses'] = []
            raise ParsingDone

    # Connections:
    _re_connections = re.compile(r"(?P<CONNECTIONS>^Connections)")

    def _parse_connections(self, line):
        if self._regex_helper.search_compiled(Ipsec._re_connections, line):
            self.connections = self._regex_helper.group('CONNECTIONS')
            self.listening_ip_addr = None
            self.current_ret['Connections'] = {}
            raise ParsingDone

    # Security Associations(1 up, 0 connecting):
    _re_security_associations = re.compile(r"(?P<SEC_ASS>^Security Associations)")

    def _parse_security_associations(self, line):
        if self._regex_helper.search_compiled(Ipsec._re_security_associations, line):
            self.security_associations = self._regex_helper.group('SEC_ASS')
            self.connections = None
            self.current_ret[self.security_associations] = {}
            raise ParsingDone

    # conn1_7:  10.1.83.64...10.1.83.4  IKEv2, dpddelay=10s
    _re_conn_key_value_key2_value2 = re.compile(
        r"^\s+(?P<CONN>\w[\w\s]*\w)\s*:\s+(?P<VALUE>\d+.\d+.\d+.\d+...\d+.\d+.\d+.\d+)\s+(?P<KEY>\S+),\s+(?P<KEY_2>\S+)=(?P<VALUE_2>\S+)$")

    def _parse_conn_key_value_key2_value2(self, line):
        if self.connections and self._regex_helper.search_compiled(Ipsec._re_conn_key_value_key2_value2, line):
            temp_conn = self._regex_helper.group('CONN')
            temp_key = self._regex_helper.group('KEY')
            temp_value = self._regex_helper.group('VALUE')
            temp_key_2 = self._regex_helper.group('KEY_2')
            temp_value_2 = self._regex_helper.group('VALUE_2')
            if temp_conn not in self.current_ret[self.connections].keys():
                self.current_ret[self.connections][temp_conn] = {}
            if temp_key not in self.current_ret[self.connections][temp_conn].keys():
                self.current_ret[self.connections][temp_conn][temp_key] = {}
            if temp_key_2 not in self.current_ret[self.connections][temp_conn].keys():
                self.current_ret[self.connections][temp_conn][temp_key_2] = {}
            self.current_ret[self.connections][temp_conn][temp_key] = temp_value
            self.current_ret[self.connections][temp_conn][temp_key_2] = temp_value_2
            raise ParsingDone

    # conn1_7:   child:  dynamic === 0.0.0.0/0 TUNNEL, dpdaction=clear
    _re_conn_key_tunnel_key2_value = re.compile(
        r"(?P<CONN>\w[\w\s]*\w)\s*:\s+(?P<KEY>\S+):\s+(?P<TUNNEL>.*)\s+TUNNEL,\s+(?P<KEY_2>\S+)=(?P<VALUE>\S+)")

    def _parse_conn_key_tunnel_key2_value(self, line):
        if self.connections and self._regex_helper.search_compiled(Ipsec._re_conn_key_tunnel_key2_value, line):
            temp_conn = self._regex_helper.group('CONN')
            temp_key = self._regex_helper.group('KEY')
            temp_tunnel = self._regex_helper.group('TUNNEL')
            temp_key_2 = self._regex_helper.group('KEY_2')
            temp_value = self._regex_helper.group('VALUE')

            if temp_key not in self.current_ret[self.connections][temp_conn].keys():
                self.current_ret[self.connections][temp_conn][temp_key] = {}
            self.current_ret[self.connections][temp_conn][temp_key]['TUNNEL'] = temp_tunnel
            self.current_ret[self.connections][temp_conn][temp_key][temp_key_2] = temp_value
            raise ParsingDone

    # conn1_7:   local:  [EA151410058.id1.nokia.com] uses public key authentication
    _re_conn_key_value = re.compile(r"^\s+(?P<CONN>\w[\w\s]*\w)\s*:\s+(?P<KEY>\S+):\s+(?P<VALUE>\S.*\S)$")

    def _parse_conn_key_value(self, line):
        if self.connections and self._regex_helper.search_compiled(Ipsec._re_conn_key_value, line):
            temp_conn = self._regex_helper.group('CONN')
            temp_key = self._regex_helper.group('KEY')
            temp_value = self._regex_helper.group('VALUE')

            if temp_key not in self.current_ret[self.connections][temp_conn].keys():
                self.current_ret[self.connections][temp_conn][temp_key] = {}
            self.current_ret[self.connections][temp_conn][temp_key] = temp_value
            raise ParsingDone

    # loaded plugins: charon aes des rc2 sha1 sha2 md5 random nonce revocation constraints pubkey pkcs1 pkcs7 pkcs8 pkcs12 pgp dnskey sshkey pem openssl fips-prf gmp xcbc cmac hmac cra curl attr kernel-netlink resolve socket-default stroke updown xauth-generic
    _re_key_value = re.compile(r"^\s+(?P<KEY>\w[\w\s]*\w)\s*:\s+(?P<VALUE>\S.*\S)$")

    def _parse_key_value(self, line):
        if self.status and self._regex_helper.search_compiled(Ipsec._re_key_value, line):
            temp_key = self._regex_helper.group('KEY')
            temp_value = self._regex_helper.group('VALUE')
            if temp_key not in self.current_ret[self.status].keys():
                self.current_ret[self.status][temp_key] = {}
            temp_value_array = temp_value.split(',')
            if temp_key == 'malloc':
                self._parse_malloc(temp_key, temp_value_array)
            elif temp_key == 'worker threads':
                self._parse_worker_threads(temp_key, temp_value_array)
            else:
                self.current_ret[self.status][temp_key] = temp_value
            raise ParsingDone

    # malloc: sbrk 1343488, mmap 0, used 345768, free 997720
    def _parse_malloc(self, temp_key, temp_value_array):
        for key_val in temp_value_array:
            key_val = key_val.strip()
            key_val_array = key_val.split(" ")
            key = key_val_array[0]
            val = key_val_array[1]
            if key not in self.current_ret[self.status][temp_key].keys():
                self.current_ret[self.status][temp_key][key] = {}
            self.current_ret[self.status][temp_key][key] = val

    # worker threads: 11 of 16 idle, 5/0/0/0 working, job queue: 0/0/0/0, scheduled: 3
    def _parse_worker_threads(self, temp_key, temp_value_array):
        for key_val in temp_value_array:
            key_val = key_val.strip()
            if ':' not in key_val:
                key = key_val.split(" ")[len(key_val.split(" ")) - 1].strip()
                val = key_val.split(key_val.split(" ")[len(key_val.split(" ")) - 1])[0].strip()
                if key not in self.current_ret[self.status][temp_key].keys():
                    self.current_ret[self.status][temp_key][key] = {}
                self.current_ret[self.status][temp_key][key] = val
            else:
                key = key_val.split(":")[0].strip()
                val = key_val.split(":")[1].strip()
                if key not in self.current_ret[self.status][temp_key].keys():
                    self.current_ret[self.status][temp_key][key] = {}
                self.current_ret[self.status][temp_key][key] = val

    # 192.168.255.129
    _re_ip_addr = re.compile(r"^\s+(?P<IP_ADDR>\S.*\S)$")

    def _parse_ip_addr(self, line):
        if self.listening_ip_addr and self._regex_helper.search_compiled(Ipsec._re_ip_addr, line):
            self.current_ret['Listening IP addresses'].append(self._regex_helper.group('IP_ADDR'))
            raise ParsingDone

    # conn1_7[1]: ESTABLISHED 93 minutes ago, 10.1.83.64[EA151410058.id1.nokia.com]...10.1.83.4[C=CN, ST=Some-State, L=NJ, O=Nokia, OU=virtualSeGW]
    _re_ike_group_established_ago_local_remote_tep = re.compile(
        r"(?P<CONN>[^\[\s]+)\[\d+\]:\s+ESTABLISHED\s+(?P<AGO>.*)\s+ago,\s+(?P<LOCAL_TEP>[\d+.]+\[.*\])...(?P<REMOTE_TEP>[\d+.]+\[.*\])$")

    def _parse_ike_group_estabilshed_ago_local_ramote_tep(self, line):
        if self.security_associations and self._regex_helper.search_compiled(
                Ipsec._re_ike_group_established_ago_local_remote_tep, line):
            temp_conn = self._regex_helper.group('CONN')
            temp_ago = self._regex_helper.group('AGO')
            temp_local_tep = self._regex_helper.group('LOCAL_TEP')
            temp_remote_tep = self._regex_helper.group('REMOTE_TEP')
            if temp_conn not in self.current_ret[self.security_associations].keys():
                self.current_ret[self.security_associations][temp_conn] = {}
            if 'IKEgroup' not in self.current_ret[self.security_associations][temp_conn].keys():
                self.current_ret[self.security_associations][temp_conn]['IKEgroup'] = {}
            self.current_ret[self.security_associations][temp_conn]['IKEgroup']['ESTABLISHED'] = {}
            self.current_ret[self.security_associations][temp_conn]['IKEgroup']['ESTABLISHED']['ago'] = temp_ago
            self.current_ret[self.security_associations][temp_conn]['IKEgroup']['ESTABLISHED'][
                'local_tunnel_endpoint'] = temp_local_tep
            self.current_ret[self.security_associations][temp_conn]['IKEgroup']['ESTABLISHED'][
                'remote_tunnel_endpoint'] = temp_remote_tep
            raise ParsingDone

    # conn1_7[1]: IKEv2 SPIs: 2c490bd4d6890edd_i* f3e4885e051cf217_r, rekeying in 22 hours
    _re_ike_group_key_value = re.compile(r"(?P<CONN>[^\[\s]+)\[\d+\]:\s+(?P<KEY>.*):\s+(?P<VALUE>.*)")

    def _parse_ike_group(self, line):
        if self.security_associations and self._regex_helper.search_compiled(Ipsec._re_ike_group_key_value, line):
            temp_conn = self._regex_helper.group('CONN')
            temp_key = self._regex_helper.group('KEY')
            temp_value = self._regex_helper.group('VALUE')

            self.current_ret[self.security_associations][temp_conn]['IKEgroup'][temp_key] = temp_value
            raise ParsingDone

    # conn1_7{1}:  INSTALLED, TUNNEL, ESP in UDP SPIs: c5434194_i c94514b4_o
    _re_child_group = re.compile(r"(?P<CONN>[^\[\s]+)\{\d+\}:\s+(?P<LINE>.*)")

    def _parse_child_group(self, line):
        if self.security_associations and self._regex_helper.search_compiled(Ipsec._re_child_group, line):
            temp_conn = self._regex_helper.group('CONN')
            temp_line = self._regex_helper.group('LINE')
            if 'CHILDgroup' not in self.current_ret[self.security_associations][temp_conn].keys():
                self.current_ret[self.security_associations][temp_conn]['CHILDgroup'] = []
            self.current_ret[self.security_associations][temp_conn]['CHILDgroup'].append(temp_line)
            raise ParsingDone


COMMAND_OUTPUT_fzm = """
toor4nsn@fzm-lsp-k2:~# ipsec statusall
Status of IKE charon daemon (strongSwan 5.2.2, Linux 4.4.112-rt127, armv7l):
  uptime: 93 minutes, since Jun 12 09:35:18 2018
  malloc: sbrk 1343488, mmap 0, used 345768, free 997720
  worker threads: 11 of 16 idle, 5/0/0/0 working, job queue: 0/0/0/0, scheduled: 3
  loaded plugins: charon aes des rc2 sha1 sha2 md5 random nonce revocation constraints pubkey pkcs1 pkcs7 pkcs8 pkcs12 pgp dnskey sshkey pem openssl fips-prf gmp xcbc cmac hmac cra curl attr kernel-netlink resolve socket-default stroke updown xauth-generic
Listening IP addresses:
  192.168.255.129
  192.168.255.16
  192.168.255.1
  192.168.255.61
  192.168.255.245
  192.168.255.241
  192.168.255.242
  10.1.83.64
  2a00:8a00:6000:7000:a59:1000:ffff:1557
Connections:
     conn1_7:  10.1.83.64...10.1.83.4  IKEv2, dpddelay=10s
     conn1_7:   local:  [EA151410058.id1.nokia.com] uses public key authentication
     conn1_7:    cert:  "C=DE, ST=Baden W\\xFCrttemberg, L=Ulm, O=NSN, OU=NWS EP RP SW PS, CN=fsmf582"
     conn1_7:   remote: uses public key authentication
     conn1_7:   child:  dynamic === 0.0.0.0/0 TUNNEL, dpdaction=clear
Security Associations (1 up, 0 connecting):
     conn1_7[1]: ESTABLISHED 93 minutes ago, 10.1.83.64[EA151410058.id1.nokia.com]...10.1.83.4[C=CN, ST=Some-State, L=NJ, O=Nokia, OU=virtualSeGW]
     conn1_7[1]: IKEv2 SPIs: 2c490bd4d6890edd_i* f3e4885e051cf217_r, rekeying in 22 hours
     conn1_7[1]: IKE proposal: AES_CBC_128/HMAC_SHA1_96/PRF_HMAC_SHA1/MODP_2048
     conn1_7{1}:  INSTALLED, TUNNEL, ESP in UDP SPIs: c5434194_i c94514b4_o
     conn1_7{1}:  AES_CBC_128/HMAC_SHA1_96, 169918 bytes_i (2224 pkts, 4s ago), 754948 bytes_o (2317 pkts, 328s ago), rekeying in 22 hours
     conn1_7{1}:   10.1.0.64/32 === 0.0.0.0/0
toor4nsn@fzm-lsp-k2:~#
"""
COMMAND_KWARGS_fzm = {'options': 'statusall'}
COMMAND_RESULT_fzm = {
    'Status of IKE charon daemon': {
        'strongSwan': '5.2.2',
        'uptime': '93 minutes, since Jun 12 09:35:18 2018',
        'malloc': {
            'sbrk': '1343488',
            'mmap': '0',
            'used': '345768',
            'free': '997720',
        },
        'worker threads': {
            'idle': '11 of 16',
            'working': '5/0/0/0',
            'job queue': '0/0/0/0',
            'scheduled': '3',
        },
        'loaded plugins': 'charon aes des rc2 sha1 sha2 md5 random nonce revocation constraints pubkey pkcs1 pkcs7 pkcs8 pkcs12 pgp dnskey sshkey pem openssl fips-prf gmp xcbc cmac hmac cra curl attr kernel-netlink resolve socket-default stroke updown xauth-generic',
    },
    'Listening IP addresses': [
        '192.168.255.129',
        '192.168.255.16',
        '192.168.255.1',
        '192.168.255.61',
        '192.168.255.245',
        '192.168.255.241',
        '192.168.255.242',
        '10.1.83.64',
        '2a00:8a00:6000:7000:a59:1000:ffff:1557',
    ],
    'Connections': {
        'conn1_7': {
            'IKEv2': '10.1.83.64...10.1.83.4',
            'dpddelay': '10s',
            'local': '[EA151410058.id1.nokia.com] uses public key authentication',
            'cert': '"C=DE, ST=Baden W\\xFCrttemberg, L=Ulm, O=NSN, OU=NWS EP RP SW PS, CN=fsmf582"',
            'remote': 'uses public key authentication',
            'child':
                {
                    'TUNNEL': 'dynamic === 0.0.0.0/0',
                    'dpdaction': 'clear',
                },
        },
    },
    'Security Associations': {
        'conn1_7': {
            'IKEgroup': {
                'ESTABLISHED': {
                    'ago': '93 minutes',
                    'local_tunnel_endpoint': '10.1.83.64[EA151410058.id1.nokia.com]',
                    'remote_tunnel_endpoint': '10.1.83.4[C=CN, ST=Some-State, L=NJ, O=Nokia, OU=virtualSeGW]',
                },
                'IKEv2 SPIs': '2c490bd4d6890edd_i* f3e4885e051cf217_r, rekeying in 22 hours',

                'IKE proposal': 'AES_CBC_128/HMAC_SHA1_96/PRF_HMAC_SHA1/MODP_2048',
            },
            'CHILDgroup': [
                'INSTALLED, TUNNEL, ESP in UDP SPIs: c5434194_i c94514b4_o',
                'AES_CBC_128/HMAC_SHA1_96, 169918 bytes_i (2224 pkts, 4s ago), 754948 bytes_o (2317 pkts, 328s ago), rekeying in 22 hours',
                '10.1.0.64/32 === 0.0.0.0/0',
            ],
        },

    },
}

COMMAND_OUTPUT_no_output = """toor4nsn@fzm-lsp-k2:~# ipsec start
Starting strongSwan 5.2.2 IPsec [starter]...
toor4nsn@fzm-lsp-k2:~#
"""
COMMAND_KWARGS_no_output = {"options": "start"}
COMMAND_RESULT_no_output = {
}
