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
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import logging
import weakref
from threading import Lock
import six

import moler.config.connections as connection_cfg
from moler.config.loggers import RAW_DATA, TRACE
from moler.exceptions import WrongUsage
from moler.helpers import instance_id


def identity_transformation(data):
    """Default coder is no encoding/decoding"""
    return data


class Connection(object):
    """Connection API required by ConnectionObservers."""

    def __init__(self, how2send=None, encoder=identity_transformation, decoder=identity_transformation,
                 name=None, newline='\n', logger_name=""):
        """
        Create Connection via registering external-IO

        :param how2send: any callable performing outgoing IO
        :param encoder: callable converting data to bytes
        :param decoder: callable restoring data from bytes
        :param name: name assigned to connection
        :param logger_name: take that logger from logging
        :param newline: new line character

        Logger is retrieved by logging.getLogger(logger_name)
        If logger_name == "" - take logger "moler.connection.<name>"
        If logger_name is None - don't use logging
        """

        super(Connection, self).__init__()
        self.how2send = how2send or self._unknown_send
        self._encoder = encoder
        self._decoder = decoder
        self._name = self._use_or_generate_name(name)
        self.newline = newline
        self.data_logger = logging.getLogger('moler.{}'.format(self.name))
        self.logger = Connection._select_logger(logger_name, self._name)

    @property
    def name(self):
        """Get name of connection"""
        return self._name

    @name.setter
    def name(self, value):
        """
        Set name of connection

        If connection is using default logger ("moler.connection.<name>")
        then modify logger after connection name change.
        """
        self._log(level=TRACE, msg=r'changing name: {} --> {}'.format(self._name, value))
        if self._using_default_logger():
            self.logger = Connection._select_logger(logger_name="", connection_name=value)
        self._name = value

    def set_data_logger(self, logger):
        self.data_logger = logger

    def __str__(self):
        return '{}(id:{})'.format(self.__class__.__name__, instance_id(self))

    def __repr__(self):
        cmd_str = self.__str__()
        # sender_str = "<Don't know>"
        sender_str = "?"
        if self.how2send != self._unknown_send:
            sender_str = repr(self.how2send)
        # return '{}, how2send {})'.format(cmd_str[:-1], sender_str)
        return '{}-->[{}]'.format(cmd_str, sender_str)

    def _use_or_generate_name(self, name):
        if name:
            return name  # use provided one
        return instance_id(self)  # generate

    @staticmethod
    def _select_logger(logger_name, connection_name):
        if logger_name is None:
            return None  # don't use logging
        default_logger_name = "moler.connection.{}".format(connection_name)
        name = logger_name or default_logger_name
        logger = logging.getLogger(name)

        if logger_name and (logger_name != default_logger_name):
            msg = "using '{}' logger - not default '{}'".format(logger_name, default_logger_name)
            logger.log(level=logging.WARNING, msg=msg)
        return logger

    def _using_default_logger(self):
        if self.logger is None:
            return False
        return self.logger.name == "moler.connection.{}".format(self._name)

    @staticmethod
    def _strip_data(data):
        return data.strip() if isinstance(data, six.string_types) else data

    # TODO: should timeout be property of IO? We timeout whole connection-observer.
    def send(self, data, timeout=30, encrypt=False):
        """Outgoing-IO API: Send data over external-IO."""
        msg = data
        if encrypt:
            length = len(data)
            msg = "*" * length

        self._log_data(msg=msg, level=logging.INFO,
                       extra={'transfer_direction': '>', 'encoder': lambda data: data.encode('utf-8')})
        self._log(level=logging.INFO,
                  msg=Connection._strip_data(msg),
                  extra={
                      'transfer_direction': '>',
                      'log_name': self.name
                  })

        encoded_msg = self.encode(msg)
        self._log_data(msg=encoded_msg, level=RAW_DATA,
                       extra={'transfer_direction': '>', 'encoder': lambda data: data.encode('utf-8')})

        encoded_data = self.encode(data)
        self.how2send(encoded_data)

    def change_newline_seq(self, newline_seq="\n"):
        """
        Method to change newline char(s). Useful when connect from one point to another if newline chars change (i.e. "\n", "\n")
        :param newline_seq: Sequence of chars to send as new line char(s)
        :return: Nothing
        """

        characters = [ord(char) for char in self.newline]
        newline_old = "0x" + ''.join("'{:02X}'".format(a) for a in characters)
        characters = [ord(char) for char in newline_seq]
        newline_new = "0x" + ''.join("'{:02X}'".format(a) for a in characters)
        # 11 15:30:32.855 DEBUG        moler.connection.UnixRemote1    |changing newline seq old '0x'0D''0A'' -> new '0x'0A''
        self._log(logging.DEBUG, "changing newline seq old '{}' -> new '{}'".format(newline_old, newline_new))
        self.newline = newline_seq

    def sendline(self, data, timeout=30, encrypt=False):
        """Outgoing-IO API: Send data line over external-IO."""
        line = data + self.newline
        self.send(data=line, timeout=timeout, encrypt=encrypt)

    def data_received(self, data):
        """Incoming-IO API: external-IO should call this method when data is received"""
        pass

    def encode(self, data):
        """Prepare data for Outgoing-IO"""
        encoded_data = self._encoder(data)
        return encoded_data

    def decode(self, data):
        """Process data from Incoming-IO"""
        decoded_data = self._decoder(data)
        return decoded_data

    def _unknown_send(self, data2send):
        err_msg = "Can't send('{}')".format(data2send)
        err_msg += "\nYou haven't installed sending method of external-IO system"
        err_msg += "\n{}: {}(how2send=external_io_send)".format("Do it either during connection construction",
                                                                self.__class__.__name__)
        err_msg += "\nor later via attribute direct set: connection.how2send = external_io_send"
        self._log(level=logging.ERROR, msg=err_msg)
        raise WrongUsage(err_msg)

    def _log_data(self, msg, level, extra=None):
        try:
            self.data_logger.log(level, msg, extra=extra)
        except Exception as err:
            print(err)  # logging errors should not propagate

    def _log(self, level, msg, extra=None):
        if self.logger:
            extra_params = {
                'log_name': self.name
            }

            if extra:
                extra_params.update(extra)
            try:
                self.logger.log(level, msg, extra=extra_params)
            except Exception as err:
                print(err)  # logging errors should not propagate


class ObservableConnection(Connection):
    """
    Allows objects to subscribe for notification about connection's data-received.
    Subscription is made by registering function to be called with this data (may be object's method).
    Function should have signature like:

    def observer(data):
        # handle that data
    """

    def __init__(self, how2send=None, encoder=identity_transformation, decoder=identity_transformation,
                 name=None, newline='\n', logger_name=""):
        """
        Create Connection via registering external-IO

        :param how2send: any callable performing outgoing IO
        :param encoder: callable converting data to bytes
        :param decoder: callable restoring data from bytes
        :param name: name assigned to connection
        :param logger_name: take that logger from logging

        Logger is retrieved by logging.getLogger(logger_name)
        If logger_name == "" - take logger "moler.connection.<name>"
        If logger_name is None - don't use logging
        """
        super(ObservableConnection, self).__init__(how2send, encoder, decoder, name=name, newline=newline,
                                                   logger_name=logger_name)
        self._observers = dict()
        self._observers_lock = Lock()

    def data_received(self, data):
        """
        Incoming-IO API:
        external-IO should call this method when data is received
        """
        self._log_data(msg=data, level=RAW_DATA,
                       extra={'transfer_direction': '<', 'encoder': lambda data: data.encode('utf-8')})

        decoded_data = self.decode(data)
        self._log_data(msg=decoded_data, level=logging.INFO,
                       extra={'transfer_direction': '<', 'encoder': lambda data: data.encode('utf-8')})

        self.notify_observers(decoded_data)

    def subscribe(self, observer):
        """
        Subscribe for 'data-received notification'
        :param observer: function to be called
        """
        with self._observers_lock:
            self._log(level=TRACE, msg="subscribe({})".format(observer))
            observer_key, value = self._get_observer_key_value(observer)

            if observer_key not in self._observers:
                self._observers[observer_key] = value

    def unsubscribe(self, observer):
        """
        Unsubscribe from 'data-received notification'
        :param observer: function that was previously subscribed
        """
        with self._observers_lock:
            self._log(level=TRACE, msg="unsubscribe({})".format(observer))
            observer_key, _ = self._get_observer_key_value(observer)
            if observer_key in self._observers:
                del self._observers[observer_key]
            else:
                self._log(level=logging.WARNING,
                          msg="{} was not subscribed".format(observer))

    def notify_observers(self, data):
        """Notify all subscribed observers about data received on connection"""
        # need copy since calling subscribers may change self._observers
        current_subscribers = list(self._observers.values())
        for self_or_none, observer_function in current_subscribers:
            try:
                self._log(level=TRACE, msg=r'notifying {}({!r})'.format(observer_function, repr(data)))
                try:
                    if self_or_none is None:
                        observer_function(data)
                    else:
                        observer_self = self_or_none
                        observer_function(observer_self, data)
                except Exception:
                    self.logger.exception(msg=r'Exception inside: {}({!r})'.format(observer_function, repr(data)))
            except ReferenceError:
                pass  # ignore: weakly-referenced object no longer exists

    @staticmethod
    def _get_observer_key_value(observer):
        """
        Subscribing methods of objects is tricky::

            class TheObserver(object):
                def __init__(self):
                    self.received_data = []

                def on_new_data(self, data):
                    self.received_data.append(data)

            observer1 = TheObserver()
            observer2 = TheObserver()

            subscribe(observer1.on_new_data)
            subscribe(observer2.on_new_data)
            subscribe(observer2.on_new_data)

        Even if it looks like 2 different subscriptions they all
        pass 3 different bound-method objects (different id()).
        So, to differentiate them we need to "unwind" out of them:
        1) self                      - 2 different id()
        2) function object of class  - all 3 have same id()

        Observer key is pair: (self-id, function-id)
        """
        try:
            self_or_none = six.get_method_self(observer)
            self_id = instance_id(self_or_none)
            self_or_none = weakref.proxy(self_or_none)
        except AttributeError:
            self_id = 0  # default for not bound methods
            self_or_none = None

        try:
            func = six.get_method_function(observer)
        except AttributeError:
            func = observer
        function_id = instance_id(func)

        observer_key = (self_id, function_id)
        observer_value = (self_or_none, weakref.proxy(func))
        return observer_key, observer_value


def _moler_logger_log(level, msg):
    logger = logging.getLogger('moler')
    logger.log(level, msg)


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


def _try_take_named_connection_params(name, io_type, **constructor_kwargs):
    if name:
        if name not in connection_cfg.named_connections:
            whats_wrong = "was not defined inside configuration"
            err_msg = "Connection named '{}' {}".format(name, whats_wrong)
            _moler_logger_log(level=logging.DEBUG, msg=err_msg)
            raise KeyError(err_msg)
        io_type, constructor_kwargs = connection_cfg.named_connections[name]
        # assume connection constructor allows 'name' parameter
        constructor_kwargs['name'] = name
    return io_type, constructor_kwargs


def _try_select_io_type_variant(io_type, variant):
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
connection_cfg.register_builtin_connections(ConnectionFactory, ObservableConnection)
connection_cfg.set_defaults()
