# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

from moler.connection import get_connection


# TODO: name, logger/logger_name as param
class Device(object):
    def __init__(self, io_connection):
        """
        Create Device communication over io_connection

        :param io_connection: External-IO connection having embedded moler-connection
        """
        self.io_connection = io_connection

    @classmethod
    def from_named_connection(cls, connection_name):
        io_conn= get_connection(name=connection_name)
        return cls(io_connection=io_conn)
