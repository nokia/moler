# -*- coding: utf-8 -*-
"""
Testing serial 2 stdin/stdout proxy

"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import importlib
import time
import serial

import pytest
import mock


# -------------- IOSerial


def test_constructing_ioserial_doesnt_open_serial_connection():
    from moler.util import moler_serial_proxy

    proxy = moler_serial_proxy.IOSerial(port="COM5")
    assert proxy._serial_connection is None


def test_opening_ioserial_correctly_constructs_serial_connection():
    from moler.util import moler_serial_proxy
    with mock.patch("moler.util.moler_serial_proxy.serial.Serial") as serial_conn:
        io = moler_serial_proxy.IOSerial(port="COM5")
        io.open()
    serial_conn.assert_called_once_with(port="COM5",
                                        baudrate=115200,
                                        stopbits=serial.STOPBITS_ONE,
                                        parity=serial.PARITY_NONE,
                                        timeout=2,
                                        xonxoff=1)


def test_closing_ioserial_correctly_closes_serial_connection(serial_connection_of_ioserial):
    from moler.util import moler_serial_proxy

    io = moler_serial_proxy.IOSerial(port="COM5")
    io.open()
    io.close()
    serial_connection_of_ioserial.close.assert_called_once_with()


def test_can_use_ioserial_as_context_manager(serial_connection_of_ioserial):
    from moler.util.moler_serial_proxy import IOSerial
    with mock.patch.object(IOSerial, "open") as io_open:
        with mock.patch.object(IOSerial, "close") as io_close:

            with IOSerial(port="COM5"):  # IOSerial may work as context manager
                io_open.assert_called_once_with()
            io_close.assert_called_once_with()

    with mock.patch.object(IOSerial, "close") as proxy_close:

        with IOSerial(port="COM5").open():  # and IOSerial.open() may work same
            pass
        proxy_close.assert_called_once_with()


def test_ioserial_can_send_data_towards_serial_connection(serial_connection_of_ioserial):
    from moler.util.moler_serial_proxy import IOSerial

    with IOSerial(port="COM5") as io:
        io.send(cmd='AT')

    serial_connection_of_ioserial.write.assert_called_once_with('AT\r\n')
    serial_connection_of_ioserial.flush.assert_called_once_with()


def test_ioserial_can_read_data_from_serial_connection(serial_connection_of_ioserial):
    from moler.util.moler_serial_proxy import IOSerial

    serial_connection_of_ioserial.readlines.return_value = ["AT\r\n", "OK"]

    with IOSerial(port="COM5") as proxy:
        response = proxy.read()

    assert response == ['AT', 'OK']


# -------------- AtConsoleProxy


def test_constructing_proxy_creates_underlying_ioserial():
    from moler.util import moler_serial_proxy
    with mock.patch("moler.util.moler_serial_proxy.IOSerial.__init__", return_value=None) as serial_io:
        moler_serial_proxy.AtConsoleProxy(port="COM5")
    serial_io.assert_called_once_with(port="COM5")


def test_opening_proxy_opens_underlying_ioserial():
    from moler.util import moler_serial_proxy

    with mock.patch("moler.util.moler_serial_proxy.IOSerial.open") as serial_io_open:
        with mock.patch("moler.util.moler_serial_proxy.AtConsoleProxy.send"):
            io = moler_serial_proxy.AtConsoleProxy(port="COM5")
            io.open()
    serial_io_open.assert_called_once_with()


def test_closing_proxy_closes_underlying_ioserial(serial_connection_of_ioserial):
    from moler.util import moler_serial_proxy
    with mock.patch("moler.util.moler_serial_proxy.IOSerial.close") as serial_io_close:
        proxy = moler_serial_proxy.AtConsoleProxy(port="COM5")
        proxy.open()
        proxy.close()
    serial_io_close.assert_called_once_with()


def test_can_use_proxy_as_context_manager(serial_connection_of_ioserial):
    from moler.util.moler_serial_proxy import AtConsoleProxy
    with mock.patch.object(AtConsoleProxy, "open") as proxy_open:
        with mock.patch.object(AtConsoleProxy, "close") as proxy_close:

            with AtConsoleProxy(port="COM5"):  # AtConsoleProxy may work as context manager
                proxy_open.assert_called_once_with()
            proxy_close.assert_called_once_with()

    with mock.patch.object(AtConsoleProxy, "close") as proxy_close:

        with AtConsoleProxy(port="COM5").open():  # and AtConsoleProxy.open() may work same
            pass
        proxy_close.assert_called_once_with()


def test_sending_over_proxy_sends_over_underlying_ioserial(serial_connection_of_ioserial):
    from moler.util.moler_serial_proxy import AtConsoleProxy

    with AtConsoleProxy(port="COM5") as proxy:
        with mock.patch("moler.util.moler_serial_proxy.IOSerial.send") as serial_io_send:
            proxy.send(cmd='AT')

    serial_io_send.assert_called_once_with('AT')


def test_opening_proxy_activates_at_echo(serial_connection_of_ioserial):
    from moler.util import moler_serial_proxy
    with mock.patch("moler.util.moler_serial_proxy.IOSerial.send") as serial_io_send:
        io = moler_serial_proxy.AtConsoleProxy(port="COM5")
        io.open()
    serial_io_send.assert_called_once_with('ATE1')


def test_reading_proxy_reads_data_from_underlying_ioserial(serial_connection_of_ioserial):
    from moler.util.moler_serial_proxy import AtConsoleProxy
    with mock.patch("moler.util.moler_serial_proxy.IOSerial.read") as serial_io_read:
        serial_io_read.return_value = ["AT", "OK"]

        with AtConsoleProxy(port="COM5") as proxy:
            response = proxy.read()

        assert response == ['AT', 'OK']


def test_proxy_can_validate_response_for_at_error():
    from moler.util.moler_serial_proxy import AtConsoleProxy

    with pytest.raises(serial.SerialException) as err:
        AtConsoleProxy.validate_no_at_error(['AT', 'ERROR'])
    assert "Response: ['AT', 'ERROR']" in str(err.value)


def test_proxy_can_check_if_at_output_is_complete():
    from moler.util.moler_serial_proxy import AtConsoleProxy

    output_1_full = AtConsoleProxy.is_at_output_complete(['AT'])
    output_2_full = AtConsoleProxy.is_at_output_complete(['AT', 'OK'])

    assert output_1_full is False
    assert output_2_full is True


def test_proxy_can_await_data_from_serial_connection_within_specified_timeout(serial_connection_of_ioserial):
    from moler.util.moler_serial_proxy import AtConsoleProxy

    def incomming_data():
        time.sleep(0.2)
        yield "AT"
        time.sleep(0.3)
        yield "OK"

    with mock.patch.object(AtConsoleProxy, "read", return_value=incomming_data()):

        with AtConsoleProxy(port="COM5") as proxy:
            response = proxy.await_response(timeout=0.6)

        assert response == ['AT', 'OK']


def test_proxy_can_timeout_if_no_complete_response_before_timeout(serial_connection_of_ioserial):
    from moler.util.moler_serial_proxy import AtConsoleProxy

    def incomming_data():
        time.sleep(0.2)
        yield "AT"
        time.sleep(0.3)
        yield "OK"


    with mock.patch.object(AtConsoleProxy, "read", return_value=incomming_data()):

        with AtConsoleProxy(port="COM5") as proxy:
            with pytest.raises(serial.SerialException) as err:
                proxy.await_response(timeout=0.4)

        assert "Awaiting serial response took" in str(err.value)
        assert "> 0.4 sec timeout" in str(err.value)
        assert "Received: ['AT', 'OK']" in str(err.value)

    with mock.patch.object(AtConsoleProxy, "read", return_value=incomming_data()):

        with AtConsoleProxy(port="COM5") as proxy:
            with pytest.raises(serial.SerialException) as err:
                proxy.await_response(timeout=0.2)

        assert "Received: ['AT']" in str(err.value)


# ----------------------------------- resources

@pytest.fixture
def serial_connection_of_ioserial():
    from serial import Serial
    with mock.patch("moler.util.moler_serial_proxy.serial.Serial") as serial_conn:  # mocking class
        serial_conn.return_value = mock.Mock(spec=Serial)  # return value from Serial() is instance of Serial
        yield serial_conn.return_value  # returning instance that will be used by calling class
