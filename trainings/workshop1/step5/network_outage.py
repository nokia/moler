import os.path
import time
from moler.config import load_config
from moler.device.device import DeviceFactory


def test_network_outage():
    load_config(config=os.path.abspath('config/my_devices.yml'))
    unix1 = DeviceFactory.get_device(name='MyMachine1')
    unix2 = DeviceFactory.get_device(name='MyMachine2')
    ping = unix1.get_cmd(cmd_name="ping", cmd_params={"destination": "localhost", "options": "-O"})
    ping.start(timeout=120)
    time.sleep(3)

    ifconfig_down = unix2.get_cmd(cmd_name="ifconfig", cmd_params={"options": "lo down"})
    sudo_ifconfig_down = unix2.get_cmd(cmd_name="sudo", cmd_params={"password": "moler", "cmd_object": ifconfig_down})
    sudo_ifconfig_down()

    time.sleep(5)

    ifconfig_up = unix2.get_cmd(cmd_name="ifconfig", cmd_params={"options": "lo up"})
    sudo_ifconfig_up = unix2.get_cmd(cmd_name="sudo", cmd_params={"password": "moler", "cmd_object": ifconfig_up})
    sudo_ifconfig_up()

    time.sleep(3)


if __name__ == '__main__':
    test_network_outage()

"""
copy this file into workshop1/network_outage.py
1. run it
2. see how we simulated network outage and restore - look at ping logs
"""
