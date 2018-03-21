# -*- coding: utf-8 -*-
"""
Connections related configuration
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


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
