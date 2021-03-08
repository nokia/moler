# -*- coding: utf-8 -*-
"""
Moler related configuration
"""
__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst, Tomasz Krol'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com, tomasz.krol@nokia.com'
import os
import six
import yaml
from contextlib import contextmanager

from moler.helpers import compare_objects
from moler.exceptions import MolerException
from moler.exceptions import WrongUsage
from . import connections as conn_cfg
from . import devices as dev_cfg
from . import loggers as log_cfg

loaded_config = ["NOT_LOADED_YET"]


@contextmanager
def read_configfile(path):
    """
    Context manager that reads content of configuration file into string

    :param path: location of configuration file
    :return: configuration file content as string
    """

    with open(path, 'r') as config_file:
        content = config_file.read()
        yield content


def read_yaml_configfile(path):
    """
    Read and convert YAML into dictionary

    :param path: location of yaml file
    :return: configuration as a python dictionary
    """
    if os.path.isabs(path):
        with read_configfile(path) as content:
            return yaml.load(content, Loader=yaml.FullLoader)
    else:
        error = "Loading configuration requires absolute path and not '{}'".format(path)
        raise MolerException(error)


def configs_are_same(config_list, config_to_find):
    """
    Utility function to check if two configs are identical (deep comparison)

    :param config_list: list of configs to compare
    :param config_to_find: second config to compare
    :return: bool, True if config_to_find is in config_list, False otherwise.
    """
    for config in config_list:
        diff = compare_objects(config, config_to_find)
        if not diff:
            return True
    return False


def load_config(config=None, from_env_var=None, *args, **kwargs):
    """
    Load Moler's configuration from config file.

    Load Moler's configuration from config file.
    :param config: either dict or config filename directly provided (overwrites 'from_env_var' if both given).
    :type config: dict or str
    :param from_env_var: name of environment variable storing config filename (file is in YAML format)
    :return: None
    """
    global loaded_config
    add_devices_only = False
    from moler.device import DeviceFactory

    if "NOT_LOADED_YET" in loaded_config:
        loaded_config = [config]
    elif not DeviceFactory.was_any_device_deleted() and configs_are_same(config_list=loaded_config,
                                                                         config_to_find=config):
        return
    else:
        # Config was already loaded and now we have to add new devices.
        add_devices_only = True
        if not configs_are_same(config_list=loaded_config, config_to_find=config):
            loaded_config.append(config)

    wrong_type_config = not isinstance(config, six.string_types) and not isinstance(config, dict)
    if config is None and from_env_var is None:
        raise WrongUsage("Provide either 'config' or 'from_env_var' parameter (none given).")
    elif (not from_env_var and wrong_type_config) or (config and wrong_type_config):
        raise WrongUsage("Unsupported config type: '{}'. Allowed are: 'dict' or 'str' holding config filename (file is in YAML format).".format(type(config)))
    if not config:
        if from_env_var not in os.environ:
            raise KeyError("Environment variable '{}' is not set".format(from_env_var))
        path = os.environ[from_env_var]
        config = read_yaml_configfile(path)
    elif isinstance(config, six.string_types):
        path = config
        config = read_yaml_configfile(path)
    # TODO: check schema
    if add_devices_only is False:
        load_logger_from_config(config)
        load_connection_from_config(config)
    load_device_from_config(config=config, add_only=add_devices_only)


def load_connection_from_config(config):
    if 'NAMED_CONNECTIONS' in config:
        for name, connection_specification in config['NAMED_CONNECTIONS'].items():
            io_type = connection_specification.pop("io_type")
            conn_cfg.define_connection(name, io_type, **connection_specification)
    if 'IO_TYPES' in config:
        if 'default_variant' in config['IO_TYPES']:
            defaults = config['IO_TYPES']['default_variant']
            for io_type, variant in defaults.items():
                conn_cfg.set_default_variant(io_type, variant)


def _load_topology(topology):
    """
    Loads topology from passed dict.

    :param topology: dict where key is devices name and value is list with names of neighbour devices.
    :return: None
    """
    if topology:
        from moler.device import DeviceFactory
        for device_name in topology:
            device = DeviceFactory.get_device(name=device_name, establish_connection=False)
            for neighbour_device_name in topology[device_name]:
                neighbour_device = DeviceFactory.get_device(name=neighbour_device_name, establish_connection=False)
                device.add_neighbour_device(neighbour_device=neighbour_device, bidirectional=True)


def load_device_from_config(config, add_only=False):
    create_at_startup = False
    topology = None
    cloned_devices = dict()
    cloned_id = 'CLONED_FROM'
    from moler.device.device import DeviceFactory

    if 'DEVICES' in config:
        if 'DEFAULT_CONNECTION' in config['DEVICES']:
            default_conn = config['DEVICES'].pop('DEFAULT_CONNECTION')
            if add_only is False:
                conn_desc = default_conn['CONNECTION_DESC']
                dev_cfg.set_default_connection(**conn_desc)

        if 'CREATE_AT_STARTUP' in config['DEVICES']:
            create_at_startup = config['DEVICES'].pop('CREATE_AT_STARTUP')

        topology = config['DEVICES'].pop('LOGICAL_TOPOLOGY', None)

        for device_name in config['DEVICES']:
            device_def = config['DEVICES'][device_name]

            # check if device name is already used
            if not _is_device_creation_needed(device_name, device_def):
                continue
            if cloned_id in device_def:
                cloned_devices[device_name] = dict()
                cloned_devices[device_name]['source'] = device_def[cloned_id]
                cloned_devices[device_name]['state'] = device_def.get('INITIAL_STATE', None)
                cloned_devices[device_name]['lazy_cmds_events'] = device_def.get('LAZY_CMDS_EVENTS', False)
            else:  # create all devices defined directly
                dev_cfg.define_device(
                    name=device_name,
                    device_class=device_def['DEVICE_CLASS'],
                    connection_desc=device_def.get('CONNECTION_DESC', dev_cfg.default_connection),
                    connection_hops={'CONNECTION_HOPS': device_def.get('CONNECTION_HOPS', {})},
                    initial_state=device_def.get('INITIAL_STATE', None),
                    lazy_cmds_events=device_def.get('LAZY_CMDS_EVENTS', False)
                )

    for device_name, device_desc in cloned_devices.items():
        cloned_from = device_desc['source']
        initial_state = device_desc['state']
        lazy_cmds_events = device_desc['lazy_cmds_events']
        DeviceFactory.get_cloned_device(source_device=cloned_from, new_name=device_name, initial_state=initial_state,
                                        establish_connection=False, lazy_cmds_events=lazy_cmds_events)
    if create_at_startup is True:
        DeviceFactory.create_all_devices()
    _load_topology(topology=topology)


def _is_device_creation_needed(name, requested_device_def):
    """

    :param name: Name of device
    :param requested_device_def: Definition of device requested to create/
    :return: True if device doesn't exist. False if device already exists.
    :
    """
    from moler.device.device import DeviceFactory
    try:
        DeviceFactory.get_device(name, establish_connection=False)
        msg = DeviceFactory.differences_between_devices_descriptions(name, requested_device_def)
        if msg:
            raise WrongUsage(msg)
        return False  # Device exists and have the same construct parameters
    except KeyError:
        return True


def load_logger_from_config(config):
    if 'LOGGER' in config:
        _config_rotating(config)
        if 'MODE' in config['LOGGER']:
            log_cfg.set_write_mode(config['LOGGER']['MODE'])
        if 'PATH' in config['LOGGER']:
            log_cfg.set_logging_path(config['LOGGER']['PATH'])
        if 'RAW_LOG' in config['LOGGER']:
            if config['LOGGER']['RAW_LOG'] is True:
                log_cfg.raw_logs_active = True
        if 'DEBUG_LEVEL' in config['LOGGER']:
            log_cfg.configure_debug_level(level=config['LOGGER']['DEBUG_LEVEL'])
        if 'DATE_FORMAT' in config['LOGGER']:
            log_cfg.set_date_format(config['LOGGER']['DATE_FORMAT'])

    log_cfg.configure_moler_main_logger()


def _config_rotating(config):
    if 'KIND' in config['LOGGER']:
        log_cfg.set_kind(config['LOGGER']['KIND'])
    if 'INTERVAL' in config['LOGGER']:
        log_cfg.set_interval(config['LOGGER']['INTERVAL'])
    if 'BACKUP_COUNT' in config['LOGGER']:
        log_cfg.set_backup_count(config['LOGGER']['BACKUP_COUNT'])


def reconfigure_logging_path(logging_path):
    """
    Set up new logging path when Moler script is running
    :param logging_path: new log path when logs will be stored
    :return:
    """
    log_cfg.reconfigure_logging_path(log_path=logging_path)


def clear():
    """Cleanup Moler's configuration"""
    global loaded_config
    loaded_config = ["NOT_LOADED_YET"]
    conn_cfg.clear()
    dev_cfg.clear()
