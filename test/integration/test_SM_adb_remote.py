__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import pytest
from moler.device import DeviceFactory


def test_adb_remote_device(loaded_adb_device_config, alternative_connection_hops, proxypc_connection_hops):
    # adb_remote = DeviceFactory.get_device(name="ADB_LHOST")
    # assert adb_remote.current_state == "UNIX_LOCAL"

    # adb_remote = DeviceFactory.get_device(name="ADB_AT_LOCALHOST", initial_state="UNIX_REMOTE",
    #                                       connection_hops=alternative_connection_hops)
    #
    # assert adb_remote.current_state == "PROXY_PC"

    adb_remote = DeviceFactory.get_device(name="ADB_LHOST", device_class="moler.device.proxy_pc2.ProxyPc2",
                                          initial_state="PROXY_PC",
                                          connection_hops=proxypc_connection_hops)

    assert adb_remote.current_state == "PROXY_PC"

    # adb_remote.goto_state("ADB_SHELL")
    # assert adb_remote.current_state == "ADB_SHELL"


def test_proxy_pc_device(loaded_proxy_pc_config, proxypc_connection_hops):
    adb_remote = DeviceFactory.get_device(name="PROXY")
    assert adb_remote.current_state == "PROXY_PC"

    adb_remote = DeviceFactory.get_device(name="PROXY",
                                          initial_state="PROXY_PC",
                                          connection_hops=proxypc_connection_hops)

    assert adb_remote.current_state == "PROXY_PC"


@pytest.fixture()
def loaded_adb_device_config():
    import yaml
    import moler.config.devices as dev_cfg
    from moler.config import load_device_from_config

    adb_dev_config_yaml = """
    DEVICES:
        ADB_LHOST:
            DEVICE_CLASS: moler.device.adbremote2.AdbRemote2
            INITIAL_STATE: UNIX_LOCAL  # ADB_SHELL
            CONNECTION_DESC:
                io_type: sshshell
                host: localhost
                username: molerssh         # change to login: to have ssh-cmd parity? username jest paramiko
                password: moler_password
            CONNECTION_HOPS:
                UNIX_LOCAL:
                    UNIX_REMOTE:
                        execute_command: ssh
                        command_params:
                            host: localhost
                            login: molerssh  # openSSH (linux ssh cmd) uzywa -l login_name
                            password: moler_password
                            expected_prompt: '$'
                UNIX_REMOTE:
                    ADB_SHELL:
                        execute_command: adb_shell
                        command_params:
                            serial_number: '1234567890'
    """
    adb_dev_config = yaml.load(adb_dev_config_yaml, Loader=yaml.FullLoader)
    load_device_from_config(adb_dev_config)

    yield
    dev_cfg.clear()


@pytest.fixture()
def loaded_proxy_pc_config():
    import yaml
    import moler.config.devices as dev_cfg
    from moler.config import load_device_from_config

    config_yaml = """
    DEVICES:
        PROXY:
            DEVICE_CLASS: moler.device.proxy_pc2.ProxyPc2
            # INITIAL_STATE: UNIX_LOCAL # incorrect for sshshell io
            CONNECTION_DESC:
                io_type: sshshell
                host: localhost
                username: molerssh         # change to login: to have ssh-cmd parity? username jest paramiko
                password: moler_password
            CONNECTION_HOPS:
                UNIX_LOCAL:
                    PROXY_PC:
                        execute_command: ssh
                        command_params:
                            host: localhost
                            login: molerssh  # openSSH (linux ssh cmd) uzywa -l login_name
                            password: moler_password
                            expected_prompt: '$'
    """
    dev_config = yaml.load(config_yaml, Loader=yaml.FullLoader)
    load_device_from_config(dev_config)

    yield
    dev_cfg.clear()


@pytest.fixture()
def alternative_connection_hops():
    import yaml

    hops_yaml = """
        UNIX_REMOTE:
            ADB_SHELL:
                execute_command: adb_shell
                command_params:
                    serial_number: '1234567890'
    """
    hops = yaml.load(hops_yaml, Loader=yaml.FullLoader)
    return hops


@pytest.fixture()
def proxypc_connection_hops():
    import yaml

    hops_yaml = """
        UNIX_LOCAL:
            PROXY_PC:
                execute_command: ssh
                command_params:
                    host: localhost
                    login: molerssh
                    password: moler_password
                    expected_prompt: '$'
    """
    hops = yaml.load(hops_yaml, Loader=yaml.FullLoader)
    return hops
