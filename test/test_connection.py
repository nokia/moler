# -*- coding: utf-8 -*-

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import binascii
import gc
from moler.util.moler_test import MolerTest

import pytest
import datetime


def do_nothing_func():
    pass


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
    from moler.connection import Connection
    from moler.exceptions import WrongUsage

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
        def data_received(self, data, recv_time):
            moler_received_data.append(data)

    m_connection = MConnection()

    class ExternalIO(object):
        def __init__(self):
            self.in_buff = ""
            self.moler_connection = m_connection

        def recv(self, bufsize):  # external-IO native naming for incoming data, f.ex. see socket
            size2read = bufsize if len(self.in_buff) >= bufsize else len(self.in_buff)
            data = self.in_buff[:size2read]
            self.moler_connection.data_received(data, datetime.datetime.now())  # external-IO feeds Moler's connection

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
        def data_received(self, data, recv_time):
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
        def data_received(self, data, recv_time):
            decoded_data = self.decode(data)
            moler_received_data.append(decoded_data)

    # compose Moler connection with external decoder
    moler_conn = WordsConnection(decoder=lambda data: data.decode("utf-8").split(" "))
    used_io = buffer_transport_class(moler_connection=moler_conn)
    used_io.write(input_bytes=b"incoming data")  # inject to buffer for next line read
    used_io.read()
    assert ["incoming", "data"] in moler_received_data


def test_can_assign_name_to_connection():
    from moler.connection import Connection

    moler_conn = Connection(name="ctrl_server")
    assert moler_conn.name == "ctrl_server"


def test_can_generate_connection_name_if_none_given():
    from moler.connection import Connection
    from moler.helpers import instance_id

    moler_conn = Connection()
    assert moler_conn.name == instance_id(moler_conn)


def test_can_use_provided_logger():
    from moler.connection import Connection
    import logging

    moler_conn = Connection(logger_name="conn.XYZ")
    assert isinstance(moler_conn.logger, logging.Logger)
    assert moler_conn.logger.name == "conn.XYZ"


def test_can_switch_off_logging():
    from moler.connection import Connection

    moler_conn = Connection(logger_name=None)
    assert moler_conn.logger is None


def test_can_use_default_logger_based_on_connection_name():
    from moler.connection import Connection
    import logging

    moler_conn = Connection(name="ABC")
    assert isinstance(moler_conn.logger, logging.Logger)
    assert moler_conn.logger.name == "moler.connection.ABC"

    moler_conn = Connection()
    assert isinstance(moler_conn.logger, logging.Logger)
    assert moler_conn.logger.name == "moler.connection.{}".format(moler_conn.name)


def test_changing_connection_name_doesnt_switch_logger_if_external_logger_used():
    from moler.connection import Connection

    moler_conn = Connection(name="ABC", logger_name="conn.ABC")
    assert moler_conn.logger.name == "conn.ABC"

    moler_conn.name = "DEF"
    assert moler_conn.logger.name == "conn.ABC"


def test_changing_connection_name_doesnt_activate_logger_if_logging_is_off():
    from moler.connection import Connection

    moler_conn = Connection(name="ABC", logger_name=None)
    assert moler_conn.logger is None

    moler_conn.name = "DEF"
    assert moler_conn.logger is None


def test_changing_connection_name_switches_logger_if_default_logger_used():
    from moler.connection import Connection

    # default logger generated internally by connection
    moler_conn = Connection(name="ABC")
    assert moler_conn.logger.name == "moler.connection.ABC"

    moler_conn.name = "DEF"
    assert moler_conn.logger.name == "moler.connection.DEF"

    # default logger via default naming
    moler_conn = Connection(name="ABC", logger_name="moler.connection.ABC")
    moler_conn.name = "DEF"
    assert moler_conn.logger.name == "moler.connection.DEF"


def test_can_notify_its_observer_about_data_comming_from_external_io(buffer_transport_class):
    from moler.threaded_moler_connection import ThreadedMolerConnection

    moler_received_data = []

    def buffer_observer(data, time_recv):
        moler_received_data.append(data)

    moler_conn = ThreadedMolerConnection()
    moler_conn.subscribe(observer=buffer_observer, connection_closed_handler=do_nothing_func)

    used_io = buffer_transport_class(moler_connection=moler_conn)  # external-IO internally sets .how2send
    used_io.write(input_bytes=b"incoming data")  # inject to buffer for next line read
    used_io.read()
    MolerTest.sleep(1, True)  # Processing in separate thread so have to wait.
    assert b"incoming data" in moler_received_data


def test_can_notify_multiple_observers_about_data_comming_from_external_io(buffer_transport_class):
    from moler.threaded_moler_connection import ThreadedMolerConnection

    class BufferObserver(object):
        def __init__(self):
            self.received_data = []

        def on_new_data(self, data, time_recv):
            self.received_data.append(data)

    buffer_observer1 = BufferObserver()
    buffer_observer2 = BufferObserver()

    moler_conn = ThreadedMolerConnection()
    moler_conn.subscribe(observer=buffer_observer1.on_new_data, connection_closed_handler=do_nothing_func)
    moler_conn.subscribe(observer=buffer_observer2.on_new_data, connection_closed_handler=do_nothing_func)

    used_io = buffer_transport_class(moler_connection=moler_conn)  # external-IO internally sets .how2send
    used_io.write(input_bytes=b"incoming data")  # inject to buffer for next line read
    used_io.read()
    MolerTest.sleep(1, True)  # Processing in separate thread so have to wait.
    assert b"incoming data" in buffer_observer1.received_data
    assert b"incoming data" in buffer_observer2.received_data


def test_notifies_only_subscribed_observers_about_data_comming_from_external_io(buffer_transport_class):
    from moler.threaded_moler_connection import ThreadedMolerConnection

    class BufferObserver(object):
        def __init__(self):
            self.received_data = []

        def on_new_data(self, data, time_recv):
            self.received_data.append(data)

    buffer_observer1 = BufferObserver()
    buffer_observer2 = BufferObserver()
    buffer_observer3 = BufferObserver()

    moler_conn = ThreadedMolerConnection()
    moler_conn.subscribe(observer=buffer_observer1.on_new_data, connection_closed_handler=do_nothing_func)
    moler_conn.subscribe(observer=buffer_observer2.on_new_data, connection_closed_handler=do_nothing_func)

    used_io = buffer_transport_class(moler_connection=moler_conn)  # external-IO internally sets .how2send
    used_io.write(input_bytes=b"incoming data")  # inject to buffer for next line read
    used_io.read()
    MolerTest.sleep(1, True)  # Processing in separate thread so have to wait.
    assert b"incoming data" in buffer_observer1.received_data
    assert b"incoming data" in buffer_observer2.received_data
    assert b"incoming data" not in buffer_observer3.received_data  # that one was not subscribed


def test_notified_observer_may_stop_subscription_of_data_comming_from_external_io(buffer_transport_class):
    from moler.threaded_moler_connection import ThreadedMolerConnection

    moler_conn = ThreadedMolerConnection()
    moler_received_data = []

    def one_time_observer(data, time_recv):
        moler_received_data.append(data)
        moler_conn.unsubscribe(observer=one_time_observer, connection_closed_handler=do_nothing_func)

    moler_conn.subscribe(observer=one_time_observer, connection_closed_handler=do_nothing_func)

    used_io = buffer_transport_class(moler_connection=moler_conn)  # external-IO internally sets .how2send
    used_io.write(input_bytes=b"data 1")  # inject to buffer for next line read
    used_io.read()
    used_io.write(input_bytes=b"data 2")  # inject to buffer for next line read
    used_io.read()
    MolerTest.sleep(1, True)  # Processing in separate thread so have to wait.
    assert b"data 1" in moler_received_data
    assert b"data 2" not in moler_received_data  # because of unsubscription during notification


def test_exception_in_observer_doesnt_break_connection_nor_other_observers(buffer_transport_class):
    from moler.threaded_moler_connection import ThreadedMolerConnection

    moler_conn = ThreadedMolerConnection()
    moler_received_data = []

    def failing_observer(data):
        raise Exception("Fail inside observer")

    def one_time_observer(data, time_recv):
        moler_received_data.append(data)
        moler_conn.unsubscribe(observer=one_time_observer, connection_closed_handler=do_nothing_func)

    moler_conn.subscribe(observer=failing_observer, connection_closed_handler=do_nothing_func)
    moler_conn.subscribe(observer=one_time_observer, connection_closed_handler=do_nothing_func)

    used_io = buffer_transport_class(moler_connection=moler_conn)  # external-IO internally sets .how2send
    used_io.write(input_bytes=b"data 1")  # inject to buffer for next line read
    used_io.read()
    moler_conn.unsubscribe(observer=failing_observer, connection_closed_handler=do_nothing_func)
    MolerTest.sleep(1, True)  # Processing in separate thread so have to wait.

    assert b"data 1" in moler_received_data


def test_repeated_unsubscription_does_nothing_but_logs_warning(buffer_transport_class):
    """
    Because of possible different concurrency models (and their races)
    we don't want to raise exception when there is already
    "no such subscription" - just put warning to logs
    """
    import time
    from moler.threaded_moler_connection import ThreadedMolerConnection

    moler_conn = ThreadedMolerConnection()
    moler_received_data = []

    def one_time_observer(data, time_recv):
        moler_received_data.append(data)
        moler_conn.unsubscribe(observer=one_time_observer, connection_closed_handler=do_nothing_func)

    moler_conn.subscribe(observer=one_time_observer, connection_closed_handler=do_nothing_func)
    # subscribe fires new thread via ObserverThreadWrapper
    # that thread pushes data: moler-connection.notify_observers() --> queue --> one_time_observer()

    used_io = buffer_transport_class(moler_connection=moler_conn)  # external-IO internally sets .how2send
    used_io.write(input_bytes=b"data 1")  # inject to buffer for next line read
    used_io.read()
    time.sleep(0.2)  # allow threads switch to let ObserverThreadWrapper push data into one_time_observer()
    moler_conn.unsubscribe(observer=one_time_observer, connection_closed_handler=do_nothing_func)  # TODO: check
    # warning in logs (when we set logging system)
    used_io.write(input_bytes=b"data 2")  # inject to buffer for next line read
    used_io.read()

    MolerTest.sleep(1, True)  # Processing in separate thread so have to wait.

    assert b"data 1" in moler_received_data
    assert b"data 2" not in moler_received_data  # because of unsubscription during notification


def test_single_unsubscription_doesnt_impact_other_subscribers():
    from moler.threaded_moler_connection import ThreadedMolerConnection

    class TheObserver(object):
        def __init__(self):
            self.received_data = []

        def on_new_data(self, data, time_recv):
            self.received_data.append(data)

    observer1 = TheObserver()
    observer2 = TheObserver()

    function_received_data = []

    def raw_fun1(data, time_recv):
        function_received_data.append(data)

    def raw_fun2(data, time_recv):
        function_received_data.append(data)

    class TheCallableClass(object):
        def __init__(self):
            self.received_data = []

        def __call__(self, data, time_recv):
            self.received_data.append(data)

    callable1 = TheCallableClass()
    callable2 = TheCallableClass()

    moler_conn = ThreadedMolerConnection()
    moler_conn.subscribe(observer=observer1.on_new_data, connection_closed_handler=do_nothing_func)
    moler_conn.subscribe(observer=observer2.on_new_data, connection_closed_handler=do_nothing_func)
    moler_conn.subscribe(observer=observer2.on_new_data, connection_closed_handler=do_nothing_func)
    moler_conn.unsubscribe(observer=observer1.on_new_data, connection_closed_handler=do_nothing_func)
    moler_conn.unsubscribe(observer=observer1.on_new_data, connection_closed_handler=do_nothing_func)

    moler_conn.subscribe(observer=raw_fun1, connection_closed_handler=do_nothing_func)
    moler_conn.subscribe(observer=raw_fun2, connection_closed_handler=do_nothing_func)
    moler_conn.subscribe(observer=raw_fun2, connection_closed_handler=do_nothing_func)
    moler_conn.unsubscribe(observer=raw_fun1, connection_closed_handler=do_nothing_func)

    moler_conn.subscribe(observer=callable1, connection_closed_handler=do_nothing_func)
    moler_conn.subscribe(observer=callable2, connection_closed_handler=do_nothing_func)
    moler_conn.subscribe(observer=callable2, connection_closed_handler=do_nothing_func)
    moler_conn.unsubscribe(observer=callable1, connection_closed_handler=do_nothing_func)

    moler_conn.data_received("incoming data", datetime.datetime.now())
    MolerTest.sleep(1, True)  # Processing in separate thread so have to wait.

    assert observer1.received_data == []
    assert observer2.received_data == ["incoming data"]

    assert function_received_data == ["incoming data"]

    assert callable1.received_data == []
    assert callable2.received_data == ["incoming data"]


def test_subscription_doesnt_block_subscriber_to_be_garbage_collected():
    from moler.threaded_moler_connection import ThreadedMolerConnection

    moler_conn = ThreadedMolerConnection()
    garbage_collected_subscribers = []

    class Subscriber(object):
        def __del__(self):
            garbage_collected_subscribers.append('Subscriber')

    class CloseSubscriber(object):
        pass

    subscr = Subscriber()
    close_subscr = CloseSubscriber()
    moler_conn.subscribe(subscr, close_subscr)

    del subscr
    gc.collect()

    assert 'Subscriber' in garbage_collected_subscribers


def test_garbage_collected_subscriber_is_not_notified():
    from moler.threaded_moler_connection import ThreadedMolerConnection

    moler_conn = ThreadedMolerConnection()
    received_data = []

    class Subscriber(object):
        def __call__(self, data, time_recv):
            received_data.append(data)

    subscr1 = Subscriber()
    subscr2 = Subscriber()
    moler_conn.subscribe(observer=subscr1, connection_closed_handler=do_nothing_func)
    moler_conn.subscribe(observer=subscr2, connection_closed_handler=do_nothing_func)

    del subscr1
    gc.collect()

    moler_conn.data_received("data", datetime.datetime.now())
    MolerTest.sleep(1, True)  # Processing in separate thread so have to wait.
    assert len(received_data) == 1

# --------------------------- resources ---------------------------


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
                self.moler_connection.data_received(data, datetime.datetime.now())  # external-IO feeds Moler's connection
    return BufferTransport
