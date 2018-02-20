# -*- coding: utf-8 -*-
# Copyright (C) 2018 Nokia
"""
:author: Grzegorz Latuszek
:contact: grzegorz.latuszek@nokia.com
"""


"""
One of Moler's goals is to be IO-agnostic.
So it can be used under twisted, asyncio, curio any any other IO system.

Moler's connection is very thin layer binding Moler's ConnectionObserver with external IO system.
Connection responsibilities:
- have a means for sending outgoing data via external IO
- have a means for receiving incoming data from external IO
- perform data encoding/decoding to let external IO use pure bytes
"""


class WrongUsage(Exception):
    """Wrong usage of library"""
    pass


def identity_transformation(data):
    """Default coder is no encoding/decoding"""
    return data


class Connection(object):
    """Connection API required by ConnectionObservers."""

    def __init__(self, how2send=None, encoder=identity_transformation, decoder=identity_transformation):
        """
        Create Connection via registering external-IO
        :param how2send: any callable performing outgoing IO
        """
        super(Connection, self).__init__()
        self.how2send = how2send or self._unknown_send
        self._encoder = encoder
        self._decoder = decoder

    def send(self, data, timeout=30):  # TODO: should timeout be property of IO? We timeout whole connection-observer.
        """Outgoing-IO API: Send data over external-IO."""
        data2send = self.encode(data)
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
        raise WrongUsage(err_msg)
