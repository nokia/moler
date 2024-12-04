# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2024, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

import logging
from threading import Lock

import transitions
from moler.helpers import ForwardingHandler

forwarding_handler = None


class StateMachine(transitions.Machine):
    def __init__(self, model='self', states=None, initial='initial', transitions=None,
                 send_event=False, auto_transitions=True,
                 ordered_transitions=False, ignore_invalid_triggers=None,
                 before_state_change=None, after_state_change=None, name=None,
                 queued=False, prepare_event=None, finalize_event=None, **kwargs):
        self._set_state_lock = Lock()
        self.state_change_log_callable = None
        self.current_state_callable = None
        super(StateMachine, self).__init__(model, states, initial, transitions, send_event, auto_transitions,
                                           ordered_transitions, ignore_invalid_triggers,
                                           before_state_change, after_state_change, name,
                                           queued, prepare_event, finalize_event, **kwargs)
        self.logger = logging.getLogger('transitions')
        self.logger.propagate = False
        self.logger.setLevel(1)

        global forwarding_handler  # pylint: disable=global-statement
        if not forwarding_handler:
            forwarding_handler = ForwardingHandler(target_logger_name="moler.state_machine")
            self.logger.addHandler(forwarding_handler)

    def set_state(self, state, model=None):
        """
        Sets state of StateMachine.

        :param state: name of state to set.
        :param model: model.
        :return: None
        """
        if self.state_change_log_callable:
            with self._set_state_lock:
                current_state = self.current_state_callable()
                if current_state != state:
                    super(StateMachine, self).set_state(state=state, model=model)
                    msg = f"Changed state from '{current_state}' into '{state}'."
                    self.state_change_log_callable(logging.INFO, msg)
        else:
            super(StateMachine, self).set_state(state=state, model=model)
