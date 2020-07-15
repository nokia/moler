# -*- coding: utf-8 -*-
"""
Package Open Source functionality of Moler.
"""
__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

named_devices = dict()
default_connection = {"io_type": "terminal", "variant": "threaded"}


def set_default_connection(io_type, variant):
    """Set connection to use as default when requesting 'device' without connection specification"""
    global default_connection
    default_connection = {"io_type": io_type, "variant": variant}


def define_device(name, device_class, connection_desc, connection_hops, initial_state=None, lazy_cmds_events=False):
    """Assign name to device specification."""
    if connection_hops:
        if "CONNECTION_HOPS" not in connection_hops.keys():
            new_connection_hops = dict()
            new_connection_hops["CONNECTION_HOPS"] = connection_hops

            connection_hops = new_connection_hops

    named_devices[name] = (device_class, connection_desc, connection_hops, initial_state, lazy_cmds_events)


def clear():
    """Cleanup configuration related to devices"""
    global default_connection
    default_connection = {"io_type": "terminal", "variant": "threaded"}
    named_devices.clear()
