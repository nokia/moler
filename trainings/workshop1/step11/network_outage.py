import os.path
import time
from moler.config import load_config
from moler.device.device import DeviceFactory
from moler.util.moler_test import MolerTest


def outage_callback(device_name):
    MolerTest.info("Network outage on {}".format(device_name))


def ping_is_on_callback():
    MolerTest.info("Ping works")


def test_network_outage():
    load_config(config=os.path.abspath('config/my_devices.yml'))
    unix1 = DeviceFactory.get_device(name='MyMachine1')
    unix2 = DeviceFactory.get_device(name='MyMachine2')

    # test setup - ensure network is up before running test
    net_up = unix2.get_cmd(cmd_name="ifconfig", cmd_params={"options": "lo up"})
    sudo_ensure_net_up = unix2.get_cmd(cmd_name="sudo", cmd_params={"password": "moler", "cmd_object": net_up})
    sudo_ensure_net_up()
    # run event observing "network down/up"
    no_ping = unix1.get_event(event_name="ping_no_response")
    no_ping.add_event_occurred_callback(callback=outage_callback,
                                        callback_params={'device_name': 'MyMachine1'})
    no_ping.start()
    ping_is_on = unix1.get_event(event_name="ping_response")
    ping_is_on.add_event_occurred_callback(callback=ping_is_on_callback, 
                                           callback_params={})
    ping_is_on.start()

    # run test
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

    # test teardown
    ping.cancel()
    no_ping.cancel()


if __name__ == '__main__':
    test_network_outage()

"""
copy this file into workshop1/network_outage.py
*** passing parameters to callback ***
1. run it
2. see logs - look for "Network outage"
"""
