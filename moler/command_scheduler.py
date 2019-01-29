# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import threading
import time
import logging
from moler.util.moler_test import MolerTest


class CommandScheduler(object):

    @staticmethod
    def add_command_to_connection(cmd, wait_for_slot=True):
        """
        Adds command to execute on connection.
        :param cmd: Command object to add to connection
        :param wait_for_slot: If True then waits till command timeout or there is free slot to execute command. If False
        then returns immediately regardless there is free slot or not.
        :return: True if command was marked as current executed, False if command cannot be set as current executed.
        """
        if CommandScheduler._add_command_to_execute(cmd=cmd):
            return True
        else:
            if wait_for_slot:
                CommandScheduler._add_command_to_queue(cmd=cmd)
                if CommandScheduler._wait_for_slot_for_command(cmd=cmd):
                    return True
                # If we are here it means command timeout before it really starts
                CommandScheduler._remove_command(cmd=cmd)
        return False

    @staticmethod
    def remove_command_from_connection(cmd):
        """
        Removes command from queue and/or current executed on connection.
        :param cmd: Command object to remove from connection
        :return: None
        """
        CommandScheduler._remove_command(cmd=cmd)

    # internal methods and variables

    _conn_lock = threading.Lock()
    _locks = dict()

    @staticmethod
    def _lock_for_connection(connection):
        with CommandScheduler._conn_lock:
            if connection not in CommandScheduler._locks:
                CommandScheduler._locks[connection] = CommandScheduler._create_empty_connection_dict()
            return CommandScheduler._locks[connection]['lock']

    @staticmethod
    def _create_empty_connection_dict():
        ret = dict()
        ret['lock'] = threading.Lock()
        ret['queue'] = list()
        ret['current_cmd'] = None
        return ret

    @staticmethod
    def _wait_for_slot_for_command(cmd):
        connection = cmd.connection
        lock = CommandScheduler._lock_for_connection(connection)
        start_time = cmd.start_time
        conn_atr = CommandScheduler._locks[connection]
        while cmd.timeout > (time.time() - start_time):
            MolerTest.sleep(seconds=0.005, quiet=True)
            with lock:
                if conn_atr['current_cmd'] is None and cmd == conn_atr['queue'][0]:
                    conn_atr['queue'].pop(0)
                    conn_atr['current_cmd'] = cmd
                    cmd._log(logging.DEBUG,
                             ">'{}' Connection.add_command_to_connection '{}' added cmd from  queue.".format(
                                 cmd, cmd.command_string))
                    return True
        return False

    @staticmethod
    def _remove_command(cmd):
        connection = cmd.connection
        lock = CommandScheduler._lock_for_connection(connection)
        conn_atr = CommandScheduler._locks[connection]
        with lock:
            if cmd == conn_atr['current_cmd']:
                conn_atr['current_cmd'] = None
            try:
                index = conn_atr['queue'].index(cmd)
                conn_atr['queue'].pop(index)
            except ValueError:  # command object does not exist in the list
                pass

    @staticmethod
    def _add_command_to_execute(cmd):
        connection = cmd.connection
        lock = CommandScheduler._lock_for_connection(connection)
        conn_atr = CommandScheduler._locks[connection]
        with lock:
            if conn_atr['current_cmd'] is None:
                conn_atr['current_cmd'] = cmd
                return True
        return False

    @staticmethod
    def _add_command_to_queue(cmd):
        connection = cmd.connection
        lock = CommandScheduler._lock_for_connection(connection)
        conn_atr = CommandScheduler._locks[connection]
        with lock:
            conn_atr['queue'].append(cmd)
