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
import weakref
from threading import Lock
import six
import logging

from moler.exceptions import WrongUsage
from moler.helpers import instance_id
from moler.config.loggers import RAW_DATA, TRACE

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


def identity_transformation(data):
    """Default coder is no encoding/decoding"""
    return data


class Connection(object):
    """Connection API required by ConnectionObservers."""

    def __init__(self, how2send=None, encoder=identity_transformation, decoder=identity_transformation,
                 name=None, logger_name=""):
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

        super(Connection, self).__init__()
        self.how2send = how2send or self._unknown_send
        self._encoder = encoder
        self._decoder = decoder
        self._name = self._use_or_generate_name(name)
        self.logger = self._select_logger(logger_name, self._name)

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
        self._log(msg=r'changing name: {} --> {}'.format(self._name, value), level=TRACE)
        if self._using_default_logger():
            self.logger = self._select_logger(logger_name="", connection_name=value)
        self._name = value

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
            msg = "using '{}' logger - not default '{}'".format(logger_name,
                                                                default_logger_name)
            logger.log(level=logging.WARNING, msg=msg)
        return logger

    def _using_default_logger(self):
        if self.logger is None:
            return False
        return self.logger.name == "moler.connection.{}".format(self._name)

    def send(self, data, timeout=30):  # TODO: should timeout be property of IO? We timeout whole connection-observer.
        """Outgoing-IO API: Send data over external-IO."""
        self._log(msg=data, level=logging.INFO, extra={'transfer_direction': '>'})
        data2send = self.encode(data)
        self._log(msg=data2send, level=RAW_DATA, extra={'transfer_direction': '>'})
        self.how2send(data2send)

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
        self._log(msg=err_msg, level=logging.ERROR)
        raise WrongUsage(err_msg)

    def _log(self, msg, level, extra=None):
        if self.logger:
            self.logger.log(level, msg, extra=extra)


class ObservableConnection(Connection):
    """
    Allows objects to subscribe for notification about connection's data-received.
    Subscription is made by registering function to be called with this data (may be object's method).
    Function should have signature like:

    def observer(data):
        # handle that data
    """

    def __init__(self, how2send=None, encoder=identity_transformation, decoder=identity_transformation,
                 name=None, logger_name=""):
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
        super(ObservableConnection, self).__init__(how2send, encoder, decoder,
                                                   name=name, logger_name=logger_name)
        self._observers = dict()
        self._observers_lock = Lock()

    def data_received(self, data):
        """
        Incoming-IO API:
        external-IO should call this method when data is received
        """
        self._log(msg=data, level=RAW_DATA, extra={'transfer_direction': '<'})
        decoded_data = self.decode(data)
        self._log(msg=decoded_data, level=logging.INFO, extra={'transfer_direction': '<'})
        self.notify_observers(decoded_data)

    def subscribe(self, observer):
        """
        Subscribe for 'data-received notification'
        :param observer: function to be called
        """
        with self._observers_lock:
            self._log(msg="subscribe({})".format(observer), level=TRACE)
            observer_key, value = self._get_observer_key_value(observer)
            if observer_key not in self._observers:
                self._observers[observer_key] = value

    def unsubscribe(self, observer):
        """
        Unsubscribe from 'data-received notification'
        :param observer: function that was previously subscribed
        """
        with self._observers_lock:
            self._log(msg="unsubscribe({})".format(observer), level=TRACE)
            observer_key, _ = self._get_observer_key_value(observer)
            if observer_key in self._observers:
                del self._observers[observer_key]
            else:
                self._log(msg="{} was not subscribed".format(observer),
                          level=logging.WARNING)

    def notify_observers(self, data):
        """Notify all subscribed observers about data received on connection"""
        # need copy since calling subscribers may change self._observers
        current_subscribers = list(self._observers.values())
        for self_or_none, observer_function in current_subscribers:
            try:
                self._log(msg=r'notifying {}({})'.format(observer_function, data), level=TRACE)
                if self_or_none is None:
                    observer_function(data)
                else:
                    observer_self = self_or_none
                    observer_function(observer_self, data)
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
            function = six.get_method_function(observer)
        except AttributeError:
            function = observer
        function_id = instance_id(function)

        observer_key = (self_id, function_id)
        observer_value = (self_or_none, weakref.proxy(function))
        return observer_key, observer_value


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
            raise ValueError(
                "constructor must be callable not {}".format(constructor))
        cls._constructors_registry[(io_type, variant)] = constructor

    @classmethod
    def get_connection(cls, io_type, variant, **constructor_kwargs):
        """
        Return connection instance of given io_type/variant

        :param io_type: 'tcp', 'memory', 'ssh', ...
        :param variant: implementation variant, ex. 'threaded', 'twisted', 'asyncio', ...
        :param constructor_kwargs: arguments specific for given io_type
        :return: None
        """
        key = (io_type, variant)
        if key not in cls._constructors_registry:
            raise KeyError(
                "No constructor registered for [{}] connection".format(key))
        constructor = cls._constructors_registry[key]
        connection = constructor(**constructor_kwargs)
        # TODO: enhance error reporting:
        # not giving port for tcp connection results in not helpful:
        # TypeError: tcp_thd_conn() takes at least 1 argument (1 given)
        # try to use funcsigs.signature to give more detailed missing-param
        return connection


def _register_builtin_connections():
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

    ConnectionFactory.register_construction(io_type="memory",
                                            variant="threaded",
                                            constructor=mem_thd_conn)
    ConnectionFactory.register_construction(io_type="tcp",
                                            variant="threaded",
                                            constructor=tcp_thd_conn)


# actions during import
_register_builtin_connections()
