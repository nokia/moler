# -*- coding: utf-8 -*-
"""
OpensslX509TextIn command test module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'

import pytest
from moler.exceptions import CommandFailure
from moler.cmd.unix.openssl_x509_text_in import OpensslX509TextIn


def test_command_raises_commandfailure_exception(buffer_connection):
    command_output = """user@server:~> openssl x509 -text -in /etc/sample.pem
    unable to load certificate
    |548039730816:error:0D0680A8:asn1 encoding routines:asn1_check_tlen:wrong tag:../openssl-1.1.1a/crypto/asn1/tasn_dec.c:1130:
    |548039730816:error:0D07803A:asn1 encoding routines:asn1_item_embed_d2i:nested asn1 error:../openssl-1.1.1a/crypto/asn1/tasn_dec.c:290:Type=X509
    |548039730816:error:0906700D:PEM routines:PEM_ASN1_read_bio:ASN1 lib:../openssl-1.1.1a/crypto/pem/pem_oth.c:33:
    user@server:~>"""
    buffer_connection.remote_inject_response([command_output])
    cmd = OpensslX509TextIn(connection=buffer_connection.moler_connection, path="/etc/sample.pem")
    with pytest.raises(CommandFailure):
        cmd()
