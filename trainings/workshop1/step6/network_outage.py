import os.path
import time
from moler.config import load_config
from moler.device.device import DeviceFactory


def test_network_outage():
    load_config(config=os.path.abspath('config/my_devices.yml'))
    unix1 = DeviceFactory.get_device(name='MyMachine1')
    unix2 = DeviceFactory.get_device(name='MyMachine2')

    # test setup - ensure network is up before running test
    ifconfig_up = unix2.get_cmd(cmd_name="ifconfig", cmd_params={"options": "lo up"})
    sudo_ifconfig_up = unix2.get_cmd(cmd_name="sudo", cmd_params={"password": "moler", "cmd_object": ifconfig_up})
    sudo_ifconfig_up()

    # run test
    ping = unix1.get_cmd(cmd_name="ping", cmd_params={"destination": "localhost", "options": "-O"})
    ping.start(timeout=120)
    time.sleep(3)

    ifconfig_down = unix2.get_cmd(cmd_name="ifconfig", cmd_params={"options": "lo down"})
    sudo_ifconfig_down = unix2.get_cmd(cmd_name="sudo", cmd_params={"password": "moler", "cmd_object": ifconfig_down})
    sudo_ifconfig_down()

    time.sleep(5)

    sudo_ifconfig_up()

    time.sleep(3)


if __name__ == '__main__':
    test_network_outage()

"""
copy this file into workshop1/network_outage.py
*** setup for test - ensure network is up before running test ***
1. run it
2. note exception - sudo_ifconfig_up() tries to run same sudo command - but remember commands are one shot only.
3. try copy sudo command creation:
    sudo_ifconfig_up = unix2.get_cmd(cmd_name="sudo", cmd_params={"password": "uteadmin", "cmd_object": ifconfig_up})
  and paste it just before second:
    sudo_ifconfig_up()
  
4. Is "one shot command" clear now?
"""
