# -*- coding: utf-8 -*-
"""
Connections related configuration
"""

__author__ = 'Grzegorz Latuszek, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, michal.ernst@nokia.com'

import platform
from moler.exceptions import MolerException

default_variant = {}
named_connections = {}


def set_default_variant(io_type, variant):
    """Set variant to use as default when requesting 'io_type' connection"""
    default_variant[io_type] = variant


def define_connection(name, io_type, **constructor_kwargs):
    """
    Assign name to connection specification.

    You should provide name that is meaningful in context of your application.
    Let's say you have 3 servers hosting HTTP under 10.20.30.41 .. 43
    Then you may name/define your connections like::

        www_svr1  io_type=tcp, host=10.20.30.41, port=80
        www_svr2  io_type=tcp, host=10.20.30.42, port=80
        www_svr3  io_type=tcp, host=10.20.30.43, port=80

    Thanks to such naming you could establish connection to server like::

        svr1_conn = get_connection(name="www_svr_1")
        svr1_conn.open()
    """
    named_connections[name] = (io_type, constructor_kwargs)


def clear():
    """Cleanup configuration related to connections"""
    default_variant.clear()
    named_connections.clear()


def set_defaults():
    set_default_variant(io_type="terminal", variant="threaded")


def register_builtin_connections(connection_factory, moler_conn_class):
    _register_builtin_connections(connection_factory, moler_conn_class)
    supported_systems = ['Linux', "FreeBSD", "Darwin", "SunOS"]

    if platform.system() in supported_systems:
        _register_builtin_unix_connections(connection_factory, moler_conn_class)
    else:
        err_msg = "Unsupported system {} detected! Supported systems: {}".format(platform.system(), supported_systems)
        raise MolerException(err_msg)


def _register_builtin_connections(connection_factory, moler_conn_class):
    from moler.io.raw.memory import ThreadedFifoBuffer
    from moler.io.raw.tcp import ThreadedTcp

    def mlr_conn_utf8(name):
        return moler_conn_class(encoder=lambda data: data.encode("utf-8"),
                                decoder=lambda data: data.decode("utf-8"),
                                name=name)

    def mem_thd_conn(name=None, echo=True, **kwargs):  # kwargs to pass  logger_name
        mlr_conn = mlr_conn_utf8(name=name)
        io_conn = ThreadedFifoBuffer(moler_connection=mlr_conn,
                                     echo=echo, name=name, *kwargs)
        return io_conn

    def tcp_thd_conn(port, host='localhost', name=None, **kwargs):  # kwargs to pass  receive_buffer_size and logger
        mlr_conn = mlr_conn_utf8(name=name)
        io_conn = ThreadedTcp(moler_connection=mlr_conn,
                              port=port, host=host, **kwargs)  # TODO: add name
        return io_conn

    # TODO: unify passing logger to io_conn (logger/logger_name - see above comments)
    connection_factory.register_construction(io_type="memory",
                                             variant="threaded",
                                             constructor=mem_thd_conn)
    connection_factory.register_construction(io_type="tcp",
                                             variant="threaded",
                                             constructor=tcp_thd_conn)


def _register_builtin_unix_connections(connection_factory, moler_conn_class):
    from moler.io.raw.terminal import ThreadedTerminal

    def mlr_conn_no_encoding(name):
        return moler_conn_class(name=name)

    def terminal_thd_conn(name=None, **constructor_kwargs):
        # ThreadedTerminal works on unicode so moler_connection must do no encoding
        mlr_conn = mlr_conn_no_encoding(name=name)
        io_conn = ThreadedTerminal(moler_connection=mlr_conn, **constructor_kwargs)  # TODO: add name, logger
        return io_conn

    # TODO: unify passing logger to io_conn (logger/logger_name)
    connection_factory.register_construction(io_type="terminal",
                                             variant="threaded",
                                             constructor=terminal_thd_conn)
