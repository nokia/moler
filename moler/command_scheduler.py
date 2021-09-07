# -*- coding: utf-8 -*-

"""Scheduler for commands and events."""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import threading
import time
import logging
from moler.exceptions import CommandTimeout
from threading import Thread


class CommandScheduler(object):
    """Scheduler for commands and events."""

    @staticmethod
    def enqueue_starting_on_connection(connection_observer):
        """
        Wait for free slot and runs command when no other command is in run mode.

        If connection_observer is not a command then runs immediately.
        :param connection_observer: Object of ConnectionObserver to run. Maybe a command or an observer.
        :return: None
        """
        scheduler = CommandScheduler._get_scheduler()
        if not connection_observer.is_command():  # Passed observer, not command.
            scheduler._submit(connection_observer)
            return
        if scheduler._add_command_to_connection(cmd=connection_observer, wait_for_slot=False):
            #  We have a free slot available
            return
        # We have to wait to finish other command(s) so let's do it in another thread.
        t1 = Thread(target=scheduler._add_command_to_connection, args=(connection_observer, True),
                    name="CommandScheduler")
        t1.setDaemon(True)
        t1.start()

    @staticmethod
    def dequeue_running_on_connection(connection_observer):
        """
        Remove command from queue and/or current executed on connection.

        :param connection_observer: Command object to remove from connection
        :return: None
        """
        if not connection_observer.is_command():  # Passed observer, not command.
            return
        scheduler = CommandScheduler._get_scheduler()
        scheduler._remove_command(cmd=connection_observer)

    @staticmethod
    def is_waiting_for_execution(connection_observer):
        """
        Check if connection_observer waits in queue before passed to runner.

        :param connection_observer: ConnectionObserver object.
        :return: True if connection_observer waits in queue and False if it does not wait.
        """
        if connection_observer.is_command:
            scheduler = CommandScheduler._get_scheduler()
            return scheduler._does_it_wait_in_queue(cmd=connection_observer)
        return False

    # internal methods and variables

    _conn_lock = threading.Lock()
    _scheduler = None

    def __init__(self):
        """Create Scheduler object."""
        with CommandScheduler._conn_lock:
            if CommandScheduler._scheduler is None:
                self._locks = dict()
                CommandScheduler._scheduler = self

    @staticmethod
    def _get_scheduler():
        """Return instance of the scheduler."""
        if CommandScheduler._scheduler is None:
            CommandScheduler()
        return CommandScheduler._scheduler

    def _add_command_to_connection(self, cmd, wait_for_slot=True):
        """
        Add command to execute on connection.

        :param cmd: Command object to add to connection
        :param wait_for_slot: If True then waits till command timeout or there is free slot to execute command. If False
        then returns immediately regardless there is free slot or not.
        :return: True if command was marked as current executed, False if command cannot be set as current executed.
        """
        if self._add_command_to_execute(cmd=cmd):
            self._submit(cmd)
            return True
        else:
            if wait_for_slot:
                self._add_command_to_queue(cmd=cmd)
                start_time = cmd.life_status.start_time
                if self._wait_for_slot_for_command(cmd=cmd):
                    self._submit(connection_observer=cmd)
                    return True
                # If we are here it means command timeout before it really starts.
                cmd.set_exception(CommandTimeout(cmd,
                                                 timeout=cmd.timeout,
                                                 kind="scheduler.await_done",
                                                 passed_time=time.time() - start_time))
                cmd.set_end_of_life()
                self._remove_command(cmd=cmd)
        return False

    def _lock_for_connection(self, connection):
        """
        Return a lock object for the connection.

        :param connection: connection to look for a lock object.
        :return: Lock object.
        """
        with CommandScheduler._conn_lock:
            if connection not in self._locks:
                self._locks[connection] = self._create_empty_connection_dict()
            return self._locks[connection]['lock']

    def _create_empty_connection_dict(self):
        """
        Create the dict with initial values for fields for connection.

        :return: Initial dict for connection
        """
        ret = dict()
        ret['lock'] = threading.Lock()
        ret['queue'] = list()
        ret['current_cmd'] = None
        return ret

    def _wait_for_slot_for_command(self, cmd):
        """
        Wait for free slot for the command.

        :param cmd: Command object.
        :return: True if command was marked as ready to execute, False if timeout.
        """
        connection = cmd.connection
        lock = self._lock_for_connection(connection)
        start_time = time.time()
        conn_atr = self._locks[connection]
        while cmd.timeout >= (time.time() - start_time):
            time.sleep(0.005)
            with lock:
                if conn_atr['current_cmd'] is None and len(conn_atr['queue']) >= 1 and cmd == conn_atr['queue'][0]:
                    conn_atr['queue'].pop(0)
                    conn_atr['current_cmd'] = cmd
                    cmd._log(logging.DEBUG,
                             ">'{}': added  added cmd ('{}') from queue.".format(
                                 cmd.connection.name, cmd))
                    return True
        return False

    def _remove_command(self, cmd):
        """
        Remove command object from queue and/or current executed.

        It is safe to call this method many times for the same command object.
        :param cmd: Command object
        :return: None.
        """
        connection = cmd.connection
        lock = self._lock_for_connection(connection)
        conn_atr = self._locks[connection]
        with lock:
            if cmd == conn_atr['current_cmd']:
                conn_atr['current_cmd'] = None
            try:
                queue = conn_atr['queue']
                index = queue.index(cmd)
                queue.pop(index)
            except ValueError:  # command object does not exist in the list
                pass

    def _add_command_to_execute(self, cmd):
        """
        Try to mark command object as current in run mode.

        :param cmd: Command object.
        :return: True if command object was marked as current run, False otherwise.
        """
        connection = cmd.connection
        lock = self._lock_for_connection(connection)
        conn_atr = self._locks[connection]
        with lock:
            if conn_atr['current_cmd'] is None:
                conn_atr['current_cmd'] = cmd
                return True
        return False

    def _add_command_to_queue(self, cmd):
        """
        Add command object to queue fot connection of command.

        :param cmd: Command object.
        :return: None.
        """
        connection = cmd.connection
        lock = self._lock_for_connection(connection)
        conn_atr = self._locks[connection]
        with lock:
            conn_atr['queue'].append(cmd)

    def _does_it_wait_in_queue(self, cmd):
        """
        Check if cmd is waiting in the queue.

        :param cmd: command to check.
        :return: True is command is waiting in the queue, False otherwise.
        """
        connection = cmd.connection
        lock = self._lock_for_connection(connection)
        conn_atr = self._locks[connection]
        with lock:
            if cmd in conn_atr['queue']:
                return True
        return False

    def _submit(self, connection_observer):
        """
        Submit a connection_observer object (command or observer) in the runner.

        :param connection_observer: Connection observer (command or observer) object to submit
        :return: None
        """
        runner = connection_observer.runner
        if not connection_observer._is_done and not runner.is_in_shutdown():
            connection_observer._future = runner.submit(connection_observer)
