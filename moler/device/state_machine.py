# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'michal.ernst@nokia.com'

import logging

import transitions
from moler.helpers import ForwardingHandler

forwarding_handler = None


class StateMachine(transitions.Machine):
    def __init__(self, model='self', states=None, initial='initial', transitions=None,
                 send_event=False, auto_transitions=True,
                 ordered_transitions=False, ignore_invalid_triggers=None,
                 before_state_change=None, after_state_change=None, name=None,
                 queued=False, prepare_event=None, finalize_event=None, **kwargs):
        self.state_change_log_callable = None
        self.current_state_callable = None
        super(StateMachine, self).__init__(model, states, initial, transitions, send_event, auto_transitions,
                                           ordered_transitions, ignore_invalid_triggers,
                                           before_state_change, after_state_change, name,
                                           queued, prepare_event, finalize_event, **kwargs)
        self.logger = logging.getLogger('transitions')
        self.logger.propagate = False
        self.logger.setLevel(1)

        global forwarding_handler
        if not forwarding_handler:
            forwarding_handler = ForwardingHandler(target_logger_name="moler.state_machine")
            self.logger.addHandler(forwarding_handler)

    def set_state(self, state, model=None):
        """
        Sets state of StateMachine.

        :param state: name of state to set.
        :param model: model.
        :return: None.
        """
        if self.state_change_log_callable:
            current_state = self.current_state_callable()
            if current_state != state:
                msg = "Changed state from '{}' into '{}.".format(current_state, state)
                self.state_change_log_callable(logging.INFO, msg)
        super(StateMachine, self).set_state(state=state, model=model)
