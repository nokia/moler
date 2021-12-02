# -*- coding: utf-8 -*-
"""
One of Moler's goals is to be IO-agnostic.
So it can be used under twisted, asyncio, curio any any other IO system.

Moler's connection is very thin layer binding Moler's ConnectionObserver with external IO system.
Connection responsibilities:
- have a means for sending outgoing data via external IO
- have a means for receiving incoming data from external IO
- perform data encoding/decoding to let external IO use pure bytes
- have a means allowing multiple observers to get it's received data (data dispatching)
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2021, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'


import logging
import platform
import moler.config.connections as connection_cfg
from moler.threaded_moler_connection import ThreadedMolerConnection  # For Moler 1.x.y
from moler.moler_connection_for_single_thread_runner import MolerConnectionForSingleThreadRunner  # Since Moler 2.0.0


def get_connection(name=None, io_type=None, variant=None, **constructor_kwargs):
    """
    Return connection instance of given io_type/variant

    :param name: name of connection defined in configuration
    :param io_type: 'tcp', 'memory', 'ssh', ...
    :param variant: implementation variant, ex. 'threaded', 'twisted', 'asyncio', ...
    :param constructor_kwargs: arguments specific for given io_type
    :return: requested connection

    You may provide either 'name' or 'io_type' but not both.
    If you provide 'name' then it is searched inside configuration
    to find io_type and constructor_kwargs assigned to that name.

    If variant is not given then it is taken from configuration.
    """
    if (not name) and (not io_type):
        err_msg = "Provide either 'name' or 'io_type' parameter (none given)"
        _moler_logger_log(level=logging.DEBUG, msg=err_msg)
        raise AssertionError(err_msg)
    if name and io_type:
        err_msg = "Use either 'name' or 'io_type' parameter (not both)"
        _moler_logger_log(level=logging.DEBUG, msg=err_msg)
        raise AssertionError(err_msg)
    io_type, constructor_kwargs = _try_take_named_connection_params(name, io_type, **constructor_kwargs)
    variant = _try_select_io_type_variant(io_type, variant)

    io_conn = _try_get_connection_with_name(io_type, variant, **constructor_kwargs)
    return io_conn


class ConnectionFactory(object):
    """
    ConnectionFactory creates plugin-system: external code can register
    "construction recipe" that will be used to create specific connection.

    "Construction recipe" means: class to be used or any other callable that can
    produce instance of connection.

    Specific means type/variant pair.
    Type is: memory, tcp, udp, ssh, ...
    Variant is: threaded, asyncio, twisted, ...

    Connection means here: external-IO-connection + moler-connection.
    Another words - fully operable connection doing IO and data dispatching,
    ready to be used by ConnectionObserver.

    ConnectionFactory responsibilities:
    - register "recipe" how to build given type/variant of connection
    - return connection instance created via utilizing registered "recipe"
    """
    _constructors_registry = {}

    @classmethod
    def register_construction(cls, io_type, variant, constructor):
        """
        Register constructor that will return "connection construction recipe"

        :param io_type: 'tcp', 'memory', 'ssh', ...
        :param variant: implementation variant, ex. 'threaded', 'twisted', 'asyncio', ...
        :param constructor: callable building connection object
        :return: None
        """
        if not callable(constructor):
            err_msg = "constructor must be callable not {}".format(constructor)
            _moler_logger_log(level=logging.DEBUG, msg=err_msg)
            raise ValueError(err_msg)
        cls._constructors_registry[(io_type, variant)] = constructor

    @classmethod
    def get_connection(cls, io_type, variant, **constructor_kwargs):
        """
        Return connection instance of given io_type/variant

        :param io_type: 'tcp', 'memory', 'ssh', ...
        :param variant: implementation variant, ex. 'threaded', 'twisted', 'asyncio', ...
        :param constructor_kwargs: arguments specific for given io_type
        :return: requested connection
        """
        key = (io_type, variant)
        if key not in cls._constructors_registry:
            err_msg = "No constructor registered for [{}] connection".format(key)
            _moler_logger_log(level=logging.DEBUG, msg=err_msg)
            raise KeyError(err_msg)
        constructor = cls._constructors_registry[key]
        connection = constructor(**constructor_kwargs)
        # TODO: enhance error reporting:
        # not giving port for tcp connection results in not helpful:
        # TypeError: tcp_thd_conn() takes at least 1 argument (1 given)
        # try to use funcsigs.signature to give more detailed missing-param
        return connection

    @classmethod
    def available_variants(cls, io_type):
        """
        Return variants available for given io_type

        :param io_type: 'tcp', 'memory', 'ssh', ...
        :return: list of variants, ex. ['threaded', 'twisted']
        """
        available = [vt for io, vt in cls._constructors_registry if io == io_type]
        return available


def _moler_logger_log(level, msg):
    logger = logging.getLogger('moler')
    logger.log(level, msg)


def _try_take_named_connection_params(name, io_type, **constructor_kwargs):
    if name:
        if name not in connection_cfg.named_connections:
            whats_wrong = "was not defined inside configuration"
            err_msg = "Connection named '{}' {}".format(name, whats_wrong)
            _moler_logger_log(level=logging.DEBUG, msg=err_msg)
            raise KeyError(err_msg)
        org_kwargs = constructor_kwargs
        io_type, constructor_kwargs = connection_cfg.named_connections[name]
        # assume connection constructor allows 'name' parameter
        constructor_kwargs['name'] = name
        # update with kwargs directly passed and not present in named_connections
        for argname in org_kwargs:
            if argname not in constructor_kwargs:
                constructor_kwargs[argname] = org_kwargs[argname]
        # TODO: shell we overwrite named_connections kwargs with the ones from org_kwargs ???
    return io_type, constructor_kwargs


def _try_select_io_type_variant(io_type, variant):
    if (io_type == 'terminal') and (platform.system() == 'Windows'):  # TODO: fix if we will have win implementation of terminal
        whats_wrong = "No '{}' connection available on Windows".format(io_type)
        fix = "try using 'sshshell' connection instead"
        err_msg = "{} ({})".format(whats_wrong, fix)
        _moler_logger_log(level=logging.DEBUG, msg=err_msg)
        raise AttributeError(err_msg)

    if variant is None:
        if io_type in connection_cfg.default_variant:
            variant = connection_cfg.default_variant[io_type]
    if variant is None:
        whats_wrong = "No variant selected"
        selection_method = "directly or via configuration"
        err_msg = "{} ({}) for '{}' connection".format(whats_wrong,
                                                       selection_method,
                                                       io_type)
        _moler_logger_log(level=logging.DEBUG, msg=err_msg)
        raise KeyError(err_msg)
    if variant not in ConnectionFactory.available_variants(io_type):
        whats_wrong = "is not registered inside ConnectionFactory"
        err_msg = "'{}' variant of '{}' connection {}".format(variant,
                                                              io_type,
                                                              whats_wrong)
        _moler_logger_log(level=logging.DEBUG, msg=err_msg)
        raise KeyError(err_msg)
    return variant


def _try_get_connection_with_name(io_type, variant, **constructor_kwargs):
    try:
        return ConnectionFactory.get_connection(io_type, variant, **constructor_kwargs)
    except TypeError as err:
        if "unexpected keyword argument 'name'" in str(err):
            # 'name' parameter not allowed in connection constructor
            del constructor_kwargs['name']
            return ConnectionFactory.get_connection(io_type, variant,
                                                    **constructor_kwargs)
        _moler_logger_log(level=logging.DEBUG, msg=repr(err))
        raise


# actions during import
# connection_cfg.register_builtin_connections(ConnectionFactory, ThreadedMolerConnection)  # Default in Moler 1.x.y
connection_cfg.register_builtin_connections(ConnectionFactory, MolerConnectionForSingleThreadRunner)  # default since
# Moler 2.0.0
connection_cfg.set_defaults()
