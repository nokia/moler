# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import logging

import transitions


class StateMachine(transitions.Machine):
    def __init__(self, model='self', states=None, initial='initial', transitions=None,
                 send_event=False, auto_transitions=True,
                 ordered_transitions=False, ignore_invalid_triggers=None,
                 before_state_change=None, after_state_change=None, name=None,
                 queued=False, prepare_event=None, finalize_event=None, **kwargs):
        super(StateMachine, self).__init__(model, states, initial, transitions, send_event, auto_transitions,
                                           ordered_transitions, ignore_invalid_triggers,
                                           before_state_change, after_state_change, name,
                                           queued, prepare_event, finalize_event, **kwargs)
        self.logger = logging.getLogger('moler.state_machine')
