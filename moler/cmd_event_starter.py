# -*- coding: utf-8 -*-
"""
CmdEventStarter
"""


__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.helpers import copy_list


class CmdEventStarter(object):
    """
    Class for starting commands and events sequentially.

    Attributes:
        None

    Methods:
        start(cmds, events): Start the given commands and events sequentially.

    """

    @classmethod
    def start(cls, cmds, events):
        """
        Start the given commands and events sequentially. The next command starts when the previous event is done.

        Args:
            cmds (list): A list of commands to start.
            events (list): A list of events to start. If None, then the next command is started immediately.

        Returns:
            None
        """
        events = copy_list(events, deep_copy=False)
        for cmd in cmds:
            try:
                event = events.pop(0)
            except IndexError:
                cmd.start()
            else:
                if event is not None:
                    event.start()
                cmd.start()
                if event is not None:
                    event.await_done()

