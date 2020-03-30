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
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import logging
import six

from moler.config.loggers import RAW_DATA, TRACE
from moler.exceptions import WrongUsage
from moler.helpers import instance_id
from moler.util.loghelper import log_into_logger


def identity_transformation(data):
    """Default coder is no encoding/decoding"""
    return data


class AbstractMolerConnection(object):
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

        super(AbstractMolerConnection, self).__init__()
        self.how2send = how2send or self._unknown_send
        self._encoder = encoder
        self._decoder = decoder
        self._name = self._use_or_generate_name(name)
        self.newline = newline
        self.data_logger = logging.getLogger('moler.{}'.format(self.name))
        self.logger = AbstractMolerConnection._select_logger(logger_name, self._name)
        self._is_open = True

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
        self._log(level=TRACE, msg=r'changing name: {} --> {}'.format(self._name, value), levels_to_go_up=2)
        if self._using_default_logger():
            self.logger = AbstractMolerConnection._select_logger(logger_name="", connection_name=value)
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
    def send(self, data, timeout=30, encrypt=False, levels_to_go_up=2):
        """Outgoing-IO API: Send data over external-IO."""
        if not self.is_open():
            return
        msg = data
        if encrypt:
            length = len(data)
            msg = "*" * length

        self._log_data(msg=msg, level=logging.INFO,
                       extra={'transfer_direction': '>', 'encoder': lambda data: data.encode('utf-8')})
        self._log(level=logging.INFO,
                  msg=AbstractMolerConnection._strip_data(msg),
                  extra={
                      'transfer_direction': '>',
                      'log_name': self.name
                  },
                  levels_to_go_up=levels_to_go_up)

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

        if self.newline != newline_seq:
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
        self.send(data=line, timeout=timeout, encrypt=encrypt, levels_to_go_up=3)

    def data_received(self, data, recv_time):
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

    def shutdown(self):
        """
        Closes connection with notifying all observers about closing.
        :return: None
        """
        self._is_open = False

    def is_open(self):
        """
        Call to check if connection is open.
        :return: True if connection is open, False otherwise.
        """
        return self._is_open

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

    def _log(self, level, msg, extra=None, levels_to_go_up=1):
        if self.logger:
            extra_params = {
                'log_name': self.name
            }

            if extra:
                extra_params.update(extra)
            try:
                # levels_to_go_up=1 : extract caller info to log where _log() has been called from
                log_into_logger(logger=self.logger, level=level, msg=msg, extra=extra_params,
                                levels_to_go_up=levels_to_go_up)
            except Exception as err:
                print(err)  # logging errors should not propagate
