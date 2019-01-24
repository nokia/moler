# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'


import threading
import time
from moler.util.moler_test import MolerTest


class CommandScheduler(object):

    @staticmethod
    def add_command_to_connection(cmd, do_not_wait=False):
        connection = cmd.connection
        lock = CommandScheduler._lock_for_connection(connection)
        conn_atr = CommandScheduler._locks[connection]
        with lock:
            if conn_atr['current_cmd'] is None:
                conn_atr['current_cmd'] = cmd
                return True
            else:
                if do_not_wait:
                    return False
                conn_atr['queue'].append(cmd)
        start_time = cmd.start_time
        while cmd.timeout > (time.time() - start_time):
            MolerTest.sleep(seconds=0.001, quiet=True)
            with lock:
                if conn_atr['current_cmd'] is None and cmd == conn_atr['queue'][0]:
                    conn_atr['queue'].pop(0)
                    conn_atr['current_cmd'] = cmd
                    self._log(logging.DEBUG,
                              ">'{}' Connection.add_command_to_connection '{}' added cmd from  queue.".format(cmd,
                                                                                                              cmd.command_string))
                    return True
        # If we are here it means command timeout before it really starts
        with lock:
            index = conn_atr['queue'].index(cmd)
            conn_atr['queue'].pop(index)
            return False

    @staticmethod
    def remove_command_form_connection(cmd):
        connection = cmd.connection
        lock = CommandScheduler._lock_for_connection(connection)
        conn_atr = CommandScheduler._locks[connection]
        with lock:
            if conn_atr['current_cmd'] == cmd:
                conn_atr['current_cmd'] = None
            try:
                index = conn_atr['queue'].index(cmd)
                conn_atr['queue'].pop(index)
            except ValueError:
                pass  # Command does not wait in the queue so nothing to remove

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
