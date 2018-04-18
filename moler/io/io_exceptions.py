# -*- coding: utf-8 -*-
"""
External-IO exceptions.

"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import platform

WIN_SOCKET_ERRORS = {
    10053: ("Software caused connection abort.",
            "An established connection was aborted by the software in your host computer,"
            " possibly due to a data transmission time-out or protocol error."),
    10054: ("Connection reset by peer.",
            "An existing connection was forcibly closed by the remote host. "
            "This normally results if the peer application on the remote host is suddenly stopped, "
            "the host is rebooted, the host or remote network interface is disabled, "
            "or the remote host uses a hard close (see setsockopt for more information on the SO_LINGER option "
            "on the remote socket). This error may also result if a connection was broken "
            "due to keep-alive activity detecting a failure while one or more operations are in progress."),
    10061: ("Connection refused.",
            "No connection could be made because the target computer actively refused it. This usually results from "
            "trying to connect to a service that is inactive on the foreign host-that is, "
            "one with no server application running.")
}


class ConnectionBaseError(Exception):
    pass


class RemoteEndpointNotConnected(ConnectionBaseError):
    pass


class RemoteEndpointDisconnected(ConnectionBaseError):
    def __init__(self, err_code=None):
        """Informs about remote endpoint disconnection"""
        self.err_code = err_code

    def __str__(self):
        if self.err_code is None:
            return "Socket closed gently"
        if platform.system() == 'Windows':
            err_str = "Windows Socket error: %d" % self.err_code
            short_meaning, long_meaning = WIN_SOCKET_ERRORS.get(self.err_code, ("", ""))
            return "%s\n%s\n%s" % (err_str, short_meaning, long_meaning)
        else:
            return "Socket error: %d" % self.err_code


class ConnectionTimeout(ConnectionBaseError):
    pass
