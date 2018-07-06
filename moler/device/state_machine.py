# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import logging

import transitions
import itertools
from functools import partial

def listify(obj):
    """Wraps a passed object into a list in case it has not been a list, tuple before.
    Returns an empty list in case ``obj`` is None.
    Args:
        obj: instance to be converted into a list.
    Returns:
        list: May also return a tuple in case ``obj`` has been a tuple before.
    """
    if obj is None:
        return []
    return obj if isinstance(obj, (list, tuple)) else [obj]

def _get_trigger(model, trigger_name, *args, **kwargs):
    """Convenience function added to the model to trigger events by name.

    Args:
        model (object): Model with assigned event trigger.
        trigger_name (str): Name of the trigger to be called.
        *args: Variable length argument list which is passed to the triggered event.
        **kwargs: Arbitrary keyword arguments which is passed to the triggered event.
    Returns:
        bool: True if a transitions has been conducted or the trigger event has been queued.
    """
    func = getattr(model, trigger_name, None)
    if func:
        return func(*args, **kwargs)
    raise AttributeError("Model has no trigger named '%s'" % trigger_name)


class Event(transitions.Event):
    def __init__(self, name, machine):
        super(Event, self).__init__(name, machine)
        self.logger = logging.getLogger('moler.state_machine')

    def _trigger(self, model, *args, **kwargs):
        """ Internal trigger function called by the ``Machine`` instance. This should not
        be called directly but via the public method ``Machine.trigger``.
        """
        state = self.machine.get_state(model.state)
        if state.name not in self.transitions:
            msg = "%sCan't trigger event %s from state %s!" % (self.machine.name, self.name,
                                                               state.name)
            if state.ignore_invalid_triggers:
                self.logger.warning(msg)
                return False
            else:
                raise transitions.MachineError(msg)
        event_data = transitions.EventData(state, self, self.machine, model, args=args, kwargs=kwargs)
        return self._process(event_data)

    def _process(self, event_data):
        for func in self.machine.prepare_event:
            self.machine.callback(func, event_data)
            self.logger.debug("Executed machine preparation callback '%s' before conditions.", func)

        try:
            for trans in self.transitions[event_data.state.name]:
                event_data.transition = trans
                if trans.execute(event_data):
                    event_data.result = True
                    break
        except Exception as err:
            event_data.error = err
            raise
        finally:
            for func in self.machine.finalize_event:
                self.machine.callback(func, event_data)
                self.logger.debug("Executed machine finalize callback '%s'.", func)
        return event_data.result


class State(transitions.State):
    def __init__(self, name, on_enter=None, on_exit=None, ignore_invalid_triggers=False):
        super(State, self).__init__(name, on_enter, on_exit, ignore_invalid_triggers)
        self.logger = logging.getLogger('moler.state_machine')

    def enter(self, event_data):
        """ Triggered when a state is entered. """
        self.logger.debug("%sEntering state %s. Processing callbacks...", event_data.machine.name, self.name)
        for handle in self.on_enter:
            event_data.machine.callback(handle, event_data)
        self.logger.info("%sEntered state %s", event_data.machine.name, self.name)

    def exit(self, event_data):
        """ Triggered when a state is exited. """
        self.logger.debug("%sExiting state %s. Processing callbacks...", event_data.machine.name, self.name)
        for handle in self.on_exit:
            event_data.machine.callback(handle, event_data)
        self.logger.info("%sExited state %s", event_data.machine.name, self.name)


class Transition(transitions.Transition):
    def __init__(self, source, dest, conditions=None, unless=None, before=None, after=None, prepare=None):
        super(Transition, self).__init__(source, dest, conditions, unless, before, after, prepare)
        self.logger = logging.getLogger('moler.state_machine')

    def execute(self, event_data):
        """ Execute the transition.
        Args:
            event_data: An instance of class EventData.
        Returns: boolean indicating whether or not the transition was
            successfully executed (True if successful, False if not).
        """
        self.logger.debug("%sInitiating transition from state %s to state %s...",
                      event_data.machine.name, self.source, self.dest)
        machine = event_data.machine

        for func in self.prepare:
            machine.callback(func, event_data)
            self.logger.debug("Executed callback '%s' before conditions.", func)

        for cond in self.conditions:
            if not cond.check(event_data):
                self.logger.debug("%sTransition condition failed: %s() does not return %s. Transition halted.",
                              event_data.machine.name, cond.func, cond.target)
                return False
        for func in itertools.chain(machine.before_state_change, self.before):
            machine.callback(func, event_data)
            self.logger.debug("%sExecuted callback '%s' before transition.", event_data.machine.name, func)

        if self.dest:  # if self.dest is None this is an internal transition with no actual state change
            self._change_state(event_data)

        for func in itertools.chain(self.after, machine.after_state_change):
            machine.callback(func, event_data)
            self.logger.debug("%sExecuted callback '%s' after transition.", event_data.machine.name, func)
        return True


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
        StateMachine.state_cls = State
        StateMachine.transition_cls = Transition
        StateMachine.event_cls = Event

    def add_model(self, model, initial=None):
        """ Register a model with the state machine, initializing triggers and callbacks. """
        models = listify(model)

        if initial is None:
            if self.initial is None:
                raise ValueError("No initial state configured for machine, must specify when adding model.")
            else:
                initial = self.initial

        for mod in models:
            mod = self if mod == 'self' else mod
            if mod not in self.models:
                if hasattr(mod, 'trigger'):
                    self.logger.warning("%sModel already contains an attribute 'trigger'. Skip method binding ",
                                    self.name)
                else:
                    mod.trigger = partial(_get_trigger, mod)

                for trigger, _ in self.events.items():
                    self._add_trigger_to_model(trigger, mod)

                for _, state in self.states.items():
                    self._add_model_to_state(state, mod)

                self.set_state(initial, model=mod)
                self.models.append(mod)
