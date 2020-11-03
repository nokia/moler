# -*- coding: utf-8 -*-
"""
s_client.

:copyright: Nokia Networks
:author: I_MOLER_DEV
:contact: I_MOLER_DEV@internal.nsn.com
:maintainer: I_MOLER_DEV
:contact: I_MOLER_DEV@internal.nsn.com
"""

import re

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.exceptions import ParsingDone

__author__ = 'Marcin Szlapa'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'marcin.szlapa@nokia.com'


class OpenSSLSClient(CommandTextualGeneric):
    """openssl command s_client"""

    def __init__(self, connection, options, prompt=None, newline_chars=None, runner=None):
        """
        s_client command.

        :param connection: moler connection to device, terminal when command is executed.
        :param options: parameters with which the command will be executed
        :param prompt: expected prompt sending by device after command execution
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        """
        super(OpenSSLSClient, self).__init__(connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.options = options
        self.current_ret["LINES"] = []

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "openssl s_client"
        cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Parse command output.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(OpenSSLSClient, self).on_new_line(line, is_full_line)

    def _parse_line(self, line):
        if not line == "":
            self.current_ret["LINES"].append(line)
        raise ParsingDone


COMMAND_OUTPUT = """openssl s_client -tls1_1 -connect 10.10.10.10:443
CONNECTED(00000003)
write:errno=0
---
no peer certificate available
---
No client certificate CA names sent
---
SSL handshake has read 0 bytes and written 10 bytes
Verification: OK
---
New, (NONE), Cipher is (NONE)
Secure Renegotiation IS NOT supported
Compression: NONE
Expansion: NONE
No ALPN negotiated
SSL-Session:
    Protocol  : TLSv1.1
    Cipher    : 0000
    Session-ID:
    Session-ID-ctx:
    Master-Key:
    PSK identity: None
    PSK identity hint: None
    SRP username: None
    Start Time: 1623194332
    Timeout   : 7200 (sec)
    Verify return code: 0 (ok)
    Extended master secret: no
---
user@host:~$"""

COMMAND_KWARGS = {
    "options": "s_client -tls1_1 -connect 10.10.10.10:443",
}

COMMAND_RESULT = {
    'LINES':
        [
            "CONNECTED(00000003)",
            "write:errno=0",
            "---",
            "no peer certificate available",
            "---",
            "No client certificate CA names sent",
            "---",
            "SSL handshake has read 0 bytes and written 10 bytes",
            "Verification: OK",
            "---",
            "New, (NONE), Cipher is (NONE)",
            "Secure Renegotiation IS NOT supported",
            "Compression: NONE",
            "Expansion: NONE",
            "No ALPN negotiated",
            "SSL-Session:",
            "    Protocol  : TLSv1.1",
            "    Cipher    : 0000",
            "    Session-ID:",
            "    Session-ID-ctx:",
            "    Master-Key:",
            "    PSK identity: None",
            "    PSK identity hint: None",
            "    SRP username: None",
            "    Start Time: 1623194332",
            "    Timeout   : 7200 (sec)",
            "    Verify return code: 0 (ok)",
            "    Extended master secret: no",
            "---",
        ],
}
