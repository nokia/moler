# -*- coding: utf-8 -*-
# Copyright (C) 2018 Nokia
"""
:author: Grzegorz Latuszek
:contact: grzegorz.latuszek@nokia.com
"""
import pytest
import binascii


def test_can_attach_external_outgoing_io_to_moler_connection():
    from moler.connection import Connection

    sent_data = []

    def write_to_external_io(data):
        sent_data.append(data)

    moler_conn = Connection(how2send=write_to_external_io)
    moler_conn.send(data="outgoing data")
    assert "outgoing data" in sent_data


def test_can_attach_instance_method_as_external_outgoing_io():
    from moler.connection import Connection

    class ExternalIO(object):
        def __init__(self):
            self.sent_data = []

        def sendall(self, data):  # external-IO native naming for outgoing data, f.ex. see socket
            self.sent_data.append(data)

    used_io = ExternalIO()
    unused_io = ExternalIO()
    moler_conn = Connection(how2send=used_io.sendall)
    moler_conn.send(data="outgoing data")
    assert "outgoing data" in used_io.sent_data
    assert "outgoing data" not in unused_io.sent_data


def test_not_attaching_external_outgoing_io_raises_exception_at_send_trial():
    from moler.connection import Connection, WrongUsage

    moler_conn = Connection()
    with pytest.raises(WrongUsage) as err:
        moler_conn.send(data="outgoing data")
    assert "Can't send('outgoing data')" in str(err.value)
    assert "You haven't installed sending method of external-IO system" in str(err.value)
    assert "Do it either during connection construction: Connection(how2send=external_io_send)" in str(err.value)
    assert "or later via attribute direct set: connection.how2send = external_io_send" in str(err.value)


def test_can_get_incomming_data_from_external_io():
    """Shows how external-IO should use Moler's connection for incoming data"""
    from moler.connection import Connection

    moler_received_data = []

    class MConnection(Connection):
        def data_received(self, data):
            moler_received_data.append(data)

    m_connection = MConnection()

    class ExternalIO(object):
        def __init__(self):
            self.in_buff = ""
            self.moler_connection = m_connection

        def recv(self, bufsize):  # external-IO native naming for incoming data, f.ex. see socket
            size2read = bufsize if len(self.in_buff) >= bufsize else len(self.in_buff)
            data = self.in_buff[:size2read]
            self.moler_connection.data_received(data)  # external-IO feeds Moler's connection

    used_io = ExternalIO()
    used_io.in_buff = "incoming data"
    used_io.recv(bufsize=8)
    assert "incoming" in moler_received_data


def test_can_encode_data_for_external_io_needs__encoder_via_inheritance():
    from moler.connection import Connection

    class ExternalIO(object):
        def __init__(self):
            self.sent_data = []

        def write(self, bytes):
            self.sent_data.append(bytes)

    class WordsConnection(Connection):
        def encode(self, data):  # takes list of words/strings
            assert isinstance(data, list)
            encoded_data = bytearray(source=" ".join(data), encoding="utf-8")
            return encoded_data  # produces bytes of space-separated words

    used_io = ExternalIO()
    m_connection = WordsConnection(how2send=used_io.write)
    m_connection.send(data=["outgoing", "data"])
    assert b"outgoing data" in used_io.sent_data


def test_can_encode_data_for_external_io_needs__encoder_via_composition():
    from moler.connection import Connection

    class ExternalIO(object):
        def __init__(self):
            self.sent_data = []

        def write(self, bytes):
            self.sent_data.append(bytes)

    used_io = ExternalIO()
    # compose Moler connection with external encoder
    hexlified_connection = Connection(how2send=used_io.write,
                                      encoder=lambda data: binascii.hexlify(bytearray(source=data, encoding="utf-8")))
    hexlified_connection.send(data="hi")  # 'h' is ASCII 0x68  'i' is ASCII 0x69
    assert b'6869' in used_io.sent_data


def test_can_decode_data_from_external_io__decoder_via_inheritance(buffer_transport_class):
    from moler.connection import Connection

    moler_received_data = []

    class WordsConnection(Connection):
        def data_received(self, data):
            decoded_data = self.decode(data)
            moler_received_data.append(decoded_data)

        def decode(self, data):
            decoded_data = data.decode("utf-8").split(" ")
            return decoded_data

    moler_conn = WordsConnection()
    used_io = buffer_transport_class(moler_connection=moler_conn)
    used_io.write(input_bytes=b"incoming data")  # inject to buffer for next line read
    used_io.read()
    assert ["incoming", "data"] in moler_received_data


def test_can_decode_data_from_external_io__decoder_via_composition(buffer_transport_class):
    from moler.connection import Connection

    moler_received_data = []

    class WordsConnection(Connection):
        def data_received(self, data):
            decoded_data = self.decode(data)
            moler_received_data.append(decoded_data)

    # compose Moler connection with external decoder
    moler_conn = WordsConnection(decoder=lambda data: data.decode("utf-8").split(" "))
    used_io = buffer_transport_class(moler_connection=moler_conn)
    used_io.write(input_bytes=b"incoming data")  # inject to buffer for next line read
    used_io.read()
    assert ["incoming", "data"] in moler_received_data


# --------------------------- resources


@pytest.fixture
def buffer_transport_class():
    """External-IO being FIFO buffer"""
    class BufferTransport(object):
        """FIFO buffer"""
        def __init__(self, moler_connection):
            self.buffer = bytearray()
            self.moler_connection = moler_connection
            self.moler_connection.how2send = self.write

        def write(self, input_bytes):
            """Add bytes to end of buffer"""
            self.buffer.extend(input_bytes)

        def read(self, bufsize=None):
            """Remove bytes from front of buffer"""
            if bufsize is None:
                size2read = len(self.buffer)
            else:
                size2read = bufsize if len(self.buffer) >= bufsize else len(self.buffer)
            if size2read > 0:
                data = self.buffer[:size2read]
                self.buffer = self.buffer[size2read:]
                self.moler_connection.data_received(data)  # external-IO feeds Moler's connection
    return BufferTransport
