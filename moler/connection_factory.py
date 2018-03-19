# -*- coding: utf-8 -*-
"""
Connection Factory creates plugin-system: external code can register
"construction recipe" that will be used to create specific connection.

"Construction recipe" means: class to be used or any other callable that can
produce instance of connection.

Specific means type/variant pair.
Type is: memory, tcp, udp, ssh, ...
Variant is: threaded, asyncio, twisted, ...

Connection means here: external-IO-connection + moler-connection.
Another words - fully operable connection doing IO and data dispatching,
ready to be used by ConnectionObserver.

Connection Factory responsibilities:
- register "recipe" how to build given type/variant of connection
- return connection instance created via utilizing registered "recipe"
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

_constructors_registry = {}


def register_construction(io_type, variant, constructor):
    """
    Register constructor that will return "connection construction recipe"

    :param io_type: 'tcp', 'memory', 'ssh', ...
    :param variant: implementation variant, ex. 'threaded', 'twisted', 'asyncio', ...
    :param constructor: callable building connection object
    :return: None
    """
    if not callable(constructor):
        raise ValueError("constructor must be callable not {}".format(constructor))
    _constructors_registry[(io_type, variant)] = constructor


def get_connection(io_type, variant, **constructor_kwargs):
    """
    Return connection instance of given io_type/variant

    :param io_type: 'tcp', 'memory', 'ssh', ...
    :param variant: implementation variant, ex. 'threaded', 'twisted', 'asyncio', ...
    :param constructor_kwargs: arguments specific for given io_type
    :return: None
    """
    key = (io_type, variant)
    if key not in _constructors_registry:
        raise KeyError("No constructor registered for [{}] connection".format(key))
    constructor = _constructors_registry[key]
    connection = constructor(**constructor_kwargs)
    # TODO: enhance error reporting:
    # not giving port for tcp connection results in not helpful:
    # TypeError: tcp_thd_conn() takes at least 1 argument (1 given)
    # try to use funcsigs.signature to give more detailed missing-param
    return connection


def _register_builtin_constructors():
    from moler.connection import ObservableConnection
    from moler.io.raw.memory import ThreadedFifoBuffer
    from moler.io.raw.tcp import ThreadedTcp

    def mlr_conn_utf8(name):
        return ObservableConnection(encoder=lambda data: data.encode("utf-8"),
                                    decoder=lambda data: data.decode("utf-8"),
                                    name=name)

    def mem_thd_conn(name=None, echo=True):
        mlr_conn = mlr_conn_utf8(name=name)
        io_conn = ThreadedFifoBuffer(moler_connection=mlr_conn,
                                     echo=echo, name=name)
        return io_conn

    def tcp_thd_conn(port, host='localhost', name=None):
        mlr_conn = mlr_conn_utf8(name=name)
        io_conn = ThreadedTcp(moler_connection=mlr_conn,
                              port=port, host=host)  # TODO: add name
        return io_conn

    register_construction(io_type="memory", variant="threaded",
                          constructor=mem_thd_conn)
    register_construction(io_type="tcp", variant="threaded",
                          constructor=tcp_thd_conn)


# actions during import
_register_builtin_constructors()
