# -*- coding: utf-8 -*-
"""
openssl_x509_text_in module.
"""

__author__ = 'Marcin Szlapa, Tomasz Krol'
__copyright__ = 'Copyright (C) 2019-2020, Nokia'
__email__ = 'marcin.szlapa@nokia.com, tomasz.krol@nokia.com'

import re
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone, CommandFailure


class OpensslX509TextIn(GenericUnixCommand):
    """Command openssl_x509_text_in."""

    def __init__(self, connection, path=None, prompt=None, newline_chars=None, runner=None):
        """
        Command openssl_x509_text_in.

        :param connection: moler connection to device, terminal when command is executed
        :param path: file path
        :param prompt: expected prompt sending by device after command execution
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        """
        super(OpensslX509TextIn, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                                runner=runner)
        self.path = path
        self._string_output = ""

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = 'openssl x509 -text -in {}'.format(self.path)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._catch_certificate_error(line)
                self._add_line_to_string_output(line)
                self._convert_string_output(line)
            except ParsingDone:
                pass
        return super(OpensslX509TextIn, self).on_new_line(line, is_full_line)

    def _add_line_to_string_output(self, line):
        """
        Add current line to string output.
        """
        self._string_output = "{}{}\n".format(self._string_output, line)

    # -----END CERTIFICATE-----
    _re_end_certificate = re.compile(r"(?P<END_CERTIFICATE>-----END CERTIFICATE-----)")

    def _convert_string_output(self, line):
        """
        Converts command output to instance of X.509 Certificate Object.
        """
        if self._regex_helper.search_compiled(OpensslX509TextIn._re_end_certificate, line):
            self.current_ret = load_pem_x509_certificate(data=self._string_output.encode(), backend=default_backend())
            raise ParsingDone

    # unable to load certificate
    _re_certificate_error = re.compile(r"(?P<CERTIFICATE_ERROR>unable\s+to\s+load\s+certificate)")

    def _catch_certificate_error(self, line):
        """
        Catch command failure and raise exception.
        """
        if self._regex_helper.search_compiled(OpensslX509TextIn._re_certificate_error, line):
            self.set_exception(CommandFailure(self, self._regex_helper.group("CERTIFICATE_ERROR")))
            raise ParsingDone


COMMAND_OUTPUT = r"""user@server:~> openssl x509 -text -in /etc/sample.pem

openssl x509 -text -in /etc/sample.pem
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 5270275 (0x506b03)
    Signature Algorithm: sha1WithRSAEncryption
        Issuer: DC=div_krk, DC=net, CN=Sub3-2
        Validity
            Not Before: Aug 29 10:00:49 2014 GMT
            Not After : Aug 13 11:20:38 2015 GMT
        Subject: DC=div_krk, DC=net, CN=Sub3-3
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (2048 bit)
                Modulus:
                    00:af:4a:67:41:dd:6d:8b:92:89:71:95:1f:cb:5b:
                    20:a6:f4:bd:11:22:b4:16:f1:6a:b5:93:21:32:cd:
                    54:62:a2:d1:af:4e:d8:48:82:55:7b:f4:bd:08:bf:
                    1e:f6:3d:af:40:5e:c5:10:32:02:e4:ff:bc:1a:c4:
                    f2:ca:20:90:4c:71:c3:cf:39:b4:a4:8a:3d:a0:71:
                    20:b7:20:8c:02:8c:d6:11:e2:35:e8:f5:6a:7e:11:
                    c3:9f:fb:ca:7e:7e:c6:b9:46:21:0e:30:e7:eb:54:
                    41:94:c1:f5:0b:2b:62:66:db:33:19:d3:fe:78:63:
                    3f:5d:e7:15:a9:17:62:86:cc:e3:03:fb:d4:dc:c5:
                    5e:82:3e:1f:1e:77:f1:f6:ea:54:5f:6f:4a:7d:61:
                    85:a6:47:02:b5:31:39:6d:d5:58:f5:54:1c:3d:2e:
                    54:6a:05:3a:7a:cd:32:42:d6:64:ca:70:cc:dc:a0:
                    84:ef:7d:35:33:dc:57:25:3b:5f:57:05:e7:33:0b:
                    f7:40:ef:92:5a:65:d1:35:ff:82:c1:83:02:e8:06:
                    7c:7e:bb:61:d7:d3:65:72:33:e7:bb:4f:59:fd:33:
                    95:2a:03:db:a5:1c:71:a4:4b:9b:cd:a0:5e:a2:a3:
                    0b:7a:03:b9:bb:f8:ed:af:37:69:25:c4:cd:c2:a8:
                    a0:ab
                Exponent: 65537 (0x10001)
        X509v3 extensions:
            X509v3 Authority Key Identifier:
                keyid:20:8B:6F:61:1C:24:57:6A:13:BD:6D:43:D0:2F:31:92:A9:8B:A0:1C

            X509v3 Subject Key Identifier:
                30:DE:91:44:E8:66:0E:24:5C:2A:95:95:29:E9:EC:96:B1:8F:D1:32
            X509v3 Key Usage: critical
                Digital Signature, Key Encipherment, Certificate Sign, CRL Sign
            X509v3 Basic Constraints: critical
                CA:TRUE
            X509v3 CRL Distribution Points:

                Full Name:
                  URI:ldap://sub3-2:389/cn=Sub3-2,dc=net,dc=div_krk?certificateRevocationList;binary???

    Signature Algorithm: sha1WithRSAEncryption
         59:65:d0:87:e7:51:5e:3c:21:db:7d:54:ba:eb:1f:7c:1c:38:
         6c:12:36:2c:79:c2:14:86:8a:be:42:9a:f4:13:c0:f8:63:06:
         93:fe:bf:16:1e:ca:d6:c6:a9:1d:ff:c5:98:42:57:3b:71:83:
         f2:d5:03:31:93:a3:8d:6b:a7:03:cb:3e:85:7a:72:52:21:a4:
         a6:ab:2f:4e:3f:23:a6:ed:3b:26:42:c8:34:bf:78:22:d2:9f:
         57:7e:73:60:0b:fd:b8:3e:1b:0e:56:93:3d:21:b3:7d:9f:71:
         1c:6f:f3:3e:ed:cc:9c:01:05:63:09:c3:11:02:a9:03:15:24:
         00:e1:48:97:30:cc:7c:b4:cc:0f:51:e8:63:c6:59:21:31:2b:
         62:72:19:81:a1:7b:da:30:89:64:77:4b:d4:64:64:85:c7:3b:
         80:de:c9:e2:24:30:aa:73:89:28:19:30:63:bd:72:30:5e:2e:
         74:d7:2e:94:09:e5:79:25:90:2f:05:47:4d:78:bb:ee:37:49:
         49:3b:55:da:96:5c:86:c1:53:cf:82:4f:18:2d:84:5c:80:f2:
         d8:cb:99:9a:11:5f:bc:d4:97:ea:70:e6:53:9e:6f:97:79:2f:
         d0:69:b6:91:9b:2b:30:38:ba:f7:4c:9d:e2:ed:d2:04:09:9b:
         4d:a9:79:d1
-----BEGIN CERTIFICATE-----
MIIDxDCCAqygAwIBAgIDUGsDMA0GCSqGSIb3DQEBBQUAMD8xFzAVBgoJkiaJk/Is
ZAEZFgdkaXZfa3JrMRMwEQYKCZImiZPyLGQBGRYDbmV0MQ8wDQYDVQQDEwZTdWIz
LTIwHhcNMTQwODI5MTAwMDQ5WhcNMTUwODEzMTEyMDM4WjA/MRcwFQYKCZImiZPy
LGQBGRYHZGl2X2tyazETMBEGCgmSJomT8ixkARkWA25ldDEPMA0GA1UEAxMGU3Vi
My0zMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAr0pnQd1ti5KJcZUf
y1sgpvS9ESK0FvFqtZMhMs1UYqLRr07YSIJVe/S9CL8e9j2vQF7FEDIC5P+8GsTy
yiCQTHHDzzm0pIo9oHEgtyCMAozWEeI16PVqfhHDn/vKfn7GuUYhDjDn61RBlMH1
CytiZtszGdP+eGM/XecVqRdihszjA/vU3MVegj4fHnfx9upUX29KfWGFpkcCtTE5
bdVY9VQcPS5UagU6es0yQtZkynDM3KCE7301M9xXJTtfVwXnMwv3QO+SWmXRNf+C
wYMC6AZ8frth19NlcjPnu09Z/TOVKgPbpRxxpEubzaBeoqMLegO5u/jtrzdpJcTN
wqigqwIDAQABo4HIMIHFMB8GA1UdIwQYMBaAFCCLb2EcJFdqE71tQ9AvMZKpi6Ac
MB0GA1UdDgQWBBQw3pFE6GYOJFwqlZUp6eyWsY/RMjAOBgNVHQ8BAf8EBAMCAaYw
DwYDVR0TAQH/BAUwAwEB/zBiBgNVHR8EWzBZMFegVaBThlFsZGFwOi8vc3ViMy0y
OjM4OS9jbj1TdWIzLTIsZGM9bmV0LGRjPWRpdl9rcms/Y2VydGlmaWNhdGVSZXZv
Y2F0aW9uTGlzdDtiaW5hcnk/Pz8wDQYJKoZIhvcNAQEFBQADggEBAFll0IfnUV48
Idt9VLrrH3wcOGwSNix5whSGir5CmvQTwPhjBpP+vxYeytbGqR3/xZhCVztxg/LV
AzGTo41rpwPLPoV6clIhpKarL04/I6btOyZCyDS/eCLSn1d+c2AL/bg+Gw5Wkz0h
s32fcRxv8z7tzJwBBWMJwxECqQMVJADhSJcwzHy0zA9R6GPGWSExK2JyGYGhe9ow
iWR3S9RkZIXHO4DeyeIkMKpziSgZMGO9cjBeLnTXLpQJ5XklkC8FR014u+43SUk7
VdqWXIbBU8+CTxgthFyA8tjLmZoRX7zUl+pw5lOeb5d5L9BptpGbKzA4uvdMneLt
0gQJm02pedE=
-----END CERTIFICATE-----

user@server:~>"""

COMMAND_KWARGS = {
    "path": "/etc/sample.pem"
}

COMMAND_RESULT = load_pem_x509_certificate(data=COMMAND_OUTPUT.encode(), backend=default_backend())
