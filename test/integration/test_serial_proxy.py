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


def test_constructing_proxy_doesnt_open_serial_connection():
    from moler.util import moler_serial_proxy

    proxy = moler_serial_proxy.SerialProxy(port="COM5")
    assert proxy._serial_connection is None


def test_opening_proxy_correctly_constructs_serial_connection():
    from moler.util import moler_serial_proxy
    with mock.patch("moler.util.moler_serial_proxy.serial.Serial") as serial_conn:
        proxy = moler_serial_proxy.SerialProxy(port="COM5")
        proxy.open()
    serial_conn.assert_called_once_with(port="COM5",
                                        baudrate=115200,
                                        stopbits=serial.STOPBITS_ONE,
                                        parity=serial.PARITY_NONE,
                                        timeout=2,
                                        xonxoff=1)


def test_closing_proxy_correctly_closes_serial_connection():
    from moler.util import moler_serial_proxy
    with mock.patch("moler.util.moler_serial_proxy.serial.Serial") as serial_conn:
        serial_conn_instance = mock.Mock()
        serial_conn.return_value = serial_conn_instance
        serial_conn_instance.close = mock.Mock()
        proxy = moler_serial_proxy.SerialProxy(port="COM5")
        proxy.open()
        proxy.close()
        serial_conn_instance.close.assert_called_once_with()


def test_can_use_proxy_as_context_manager():
    from moler.util.moler_serial_proxy import SerialProxy
    with mock.patch.object(SerialProxy, "open") as proxy_open:
        with mock.patch.object(SerialProxy, "close") as proxy_close:

            with SerialProxy(port="COM5"):  # SerialProxy may work as context manager
                proxy_open.assert_called_once_with()
            proxy_close.assert_called_once_with()

    with mock.patch("moler.util.moler_serial_proxy.serial.Serial"):
        with mock.patch.object(SerialProxy, "close") as proxy_close:

            with SerialProxy(port="COM5").open():  # and SerialProxy.open() may work same
                pass
            proxy_close.assert_called_once_with()


def test_proxy_can_send_data_towards_serial_connection():
    from moler.util.moler_serial_proxy import SerialProxy
    with mock.patch("moler.util.moler_serial_proxy.serial.Serial") as serial_conn:
        serial_conn_instance = mock.Mock()
        serial_conn.return_value = serial_conn_instance
        serial_conn_instance.write = mock.Mock()
        serial_conn_instance.flush = mock.Mock()

        with SerialProxy(port="COM5") as proxy:
            proxy.send(cmd='AT')

        serial_conn_instance.write.assert_called_once_with('AT\r\n')
        serial_conn_instance.flush.assert_called_once_with()


def test_proxy_can_read_data_from_serial_connection():
    from moler.util.moler_serial_proxy import SerialProxy
    with mock.patch("moler.util.moler_serial_proxy.serial.Serial") as serial_conn:
        serial_conn_instance = mock.Mock()
        serial_conn.return_value = serial_conn_instance
        serial_conn_instance.readlines = mock.Mock()
        serial_conn_instance.readlines.return_value = ["AT\r\n", "OK"]

        with SerialProxy(port="COM5") as proxy:
            response = proxy.read()

        assert response == ['AT', 'OK']


def test_proxy_can_validate_response_for_at_error():
    from moler.util.moler_serial_proxy import SerialProxy

    with pytest.raises(serial.SerialException) as err:
        SerialProxy.validate_no_at_error(['AT', 'ERROR'])
    assert "Response: ['AT', 'ERROR']" in str(err.value)


def test_proxy_can_check_if_at_output_is_complete():
    from moler.util.moler_serial_proxy import SerialProxy

    output_1_full = SerialProxy.is_at_output_complete(['AT'])
    output_2_full = SerialProxy.is_at_output_complete(['AT', 'OK'])

    assert output_1_full is False
    assert output_2_full is True


def test_proxy_can_await_data_from_serial_connection_within_specified_timeout():
    from moler.util.moler_serial_proxy import SerialProxy

    def incomming_data():
        time.sleep(0.2)
        yield "AT"
        time.sleep(0.3)
        yield "OK"

    with mock.patch("moler.util.moler_serial_proxy.serial.Serial"):
        with mock.patch.object(SerialProxy, "read", return_value=incomming_data()):

            with SerialProxy(port="COM5") as proxy:
                response = proxy.await_response(timeout=0.6)

            assert response == ['AT', 'OK']


def test_proxy_can_timeout_if_no_complete_response_before_timeout():
    from moler.util.moler_serial_proxy import SerialProxy

    def incomming_data():
        time.sleep(0.2)
        yield "AT"
        time.sleep(0.3)
        yield "OK"

    with mock.patch("moler.util.moler_serial_proxy.serial.Serial"):
        with mock.patch.object(SerialProxy, "read", return_value=incomming_data()):

            with SerialProxy(port="COM5") as proxy:
                with pytest.raises(serial.SerialException) as err:
                    proxy.await_response(timeout=0.4)

            assert "Awaiting serial response took" in str(err.value)
            assert "> 0.4 sec timeout" in str(err.value)
            assert "Received: ['AT', 'OK']" in str(err.value)

        with mock.patch.object(SerialProxy, "read", return_value=incomming_data()):

            with SerialProxy(port="COM5") as proxy:
                with pytest.raises(serial.SerialException) as err:
                    proxy.await_response(timeout=0.2)

            assert "Received: ['AT']" in str(err.value)
