# -*- coding: utf-8 -*-
"""
Command is a type of ConnectionObserver.
Additionally:
- it starts by sending command string over connection - starting CMD(*)
- it focuses on parsing the output caused by that CMD
- it stores string starting that CMD inside .command_string attribute

(*) we use naming CMD to differentiate from Command class naming:
- CMD - command started on some device like 'ls -l' that has its own output
- Command - Python code automating its startup/parsing/completion
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

from moler.connection_observer import ConnectionObserver
from moler.exceptions import NoCommandStringProvided
from moler.helpers import instance_id


class Command(ConnectionObserver):
    def __init__(self, connection=None, runner=None):
        """
        Create instance of Command class
        :param connection: connection used to start CMD and receive its output
        """
        super(Command, self).__init__(connection=connection, runner=runner)
        self.command_string = ''
        self.cmd_name = Command.observer_name

    def __str__(self):
        cmd_str = self.command_string if self.command_string else '<EMPTY COMMAND STRING>'
        if cmd_str[-1] == '\n':
            cmd_str = cmd_str[:-1] + r'<\n>'
        return '{}("{}", id:{})'.format(self.__class__.__name__, cmd_str, instance_id(self))

    def start(self, timeout=None, *args, **kwargs):
        """Start background execution of command."""
        self._validate_start(*args, **kwargs)
        ret = super(Command, self).start(timeout, *args, **kwargs)
        self._is_running = True  # when it sends - real CMD starts running
        return ret

    def add_command_to_connection(self):
        """
        Adds Command object to connection.
        :return: True if ConnectionObserver was added to connection. False if cannot add Command to connection in timeout.
        """
        if self.connection.add_command_to_connection(cmd=self):
            return True
        return False

    def remove_command_from_connection(self):
        """
        Removes blocking Command object from connection.
        :return: Nothing
        """
        self.connection.remove_command_from_connection(cmd=self)

    def is_blocking_observer(self):
        """
        :return: True if instance of ConnectionObserver is a blocking one (a command). False if not blocking.
        """
        return True

    def _validate_start(self, *args, **kwargs):
        # check base class invariants first
        super(Command, self)._validate_start(*args, **kwargs)
        # then what is needed for command
        if not self.command_string:
            # no chance to start CMD
            raise NoCommandStringProvided(self)

    def get_long_desc(self):
        return "Command '{}.{}':'{}'".format(self.__class__.__module__, self.__class__.__name__, self.command_string)

    def get_short_desc(self):
        return "Command '{}.{}'".format(self.__class__.__module__, self.__class__.__name__)
