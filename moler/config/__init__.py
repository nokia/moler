# -*- coding: utf-8 -*-
"""
Moler related configuration
"""
__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'
import os
import six
import yaml
from contextlib import contextmanager

from moler.helpers import compare_objects
from moler.exceptions import MolerException
from . import connections as conn_cfg
from . import devices as dev_cfg
from . import loggers as log_cfg

loaded_config = "NOT_LOADED_YET"


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


def configs_are_same(config1, config2):
    """
    Utility function to check if two configs are identical (deep comparison)

    :param config1: first config to compare
    :param config2: second config to compare
    :return: bool
    """
    diff = compare_objects(config1, config2)
    return not diff


def load_config(config=None, from_env_var=None, config_type='yaml'):
    """
    Load Moler's configuration from config file

    :param config: either dict or config filename directly provided (overwrites 'from_env_var' if both given)
    :param from_env_var: name of environment variable storing config filename
    :param config_type: 'dict' ('config' param is dict) or 'yaml' ('config' is filename of file with YAML content)
    :return: None
    """
    global loaded_config

    if loaded_config == "NOT_LOADED_YET":
        loaded_config = config
    elif configs_are_same(loaded_config, config):
        return
    else:
        why = "Reloading configuration during Moler execution is not supported!"
        error = "Trial to load '{}' config while '{}' config already loaded.\n{}".format(config, loaded_config, why)
        raise MolerException(error)

    assert (config_type == 'dict') or (config_type == 'yaml')  # no other format supported yet
    if not config:
        if not from_env_var:
            raise AssertionError("Provide either 'config' or 'from_env_var' parameter (none given)")
        if from_env_var not in os.environ:
            raise KeyError("Environment variable '{}' is not set".format(from_env_var))
        path = os.environ[from_env_var]
        config = read_yaml_configfile(path)
    elif config_type == 'yaml':
        assert isinstance(config, six.string_types)
        path = config
        config = read_yaml_configfile(path)
    elif config_type == 'dict':
        assert isinstance(config, dict)
    # TODO: check schema
    load_logger_from_config(config)
    load_connection_from_config(config)
    load_device_from_config(config)


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


def load_device_from_config(config):
    create_at_startup = False

    if 'DEVICES' in config:
        if 'DEFAULT_CONNECTION' in config['DEVICES']:
            default_conn = config['DEVICES'].pop('DEFAULT_CONNECTION')
            conn_desc = default_conn['CONNECTION_DESC']
            dev_cfg.set_default_connection(**conn_desc)

        if 'CREATE_AT_STARTUP' in config['DEVICES']:
            create_at_startup = config['DEVICES'].pop('CREATE_AT_STARTUP')

        for device_name in config['DEVICES']:
            device_def = config['DEVICES'][device_name]
            dev_cfg.define_device(
                name=device_name,
                device_class=device_def['DEVICE_CLASS'],
                connection_desc=device_def.get('CONNECTION_DESC', dev_cfg.default_connection),
                connection_hops={'CONNECTION_HOPS': device_def.get('CONNECTION_HOPS', {})},
                initial_state=device_def.get('INITIAL_STATE', None),
            )

    if create_at_startup is True:
        from moler.device.device import DeviceFactory
        DeviceFactory.create_all_devices()


def load_logger_from_config(config):
    if 'LOGGER' in config:
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
    loaded_config = "NOT_LOADED_YET"
    conn_cfg.clear()
    dev_cfg.clear()
