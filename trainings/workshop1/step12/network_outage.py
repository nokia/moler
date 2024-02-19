import os.path
import time
from moler.config import load_config
from moler.device.device import DeviceFactory
from moler.util.moler_test import MolerTest


def outage_callback(device_name, ping_times):
    MolerTest.info(f"Network outage on {device_name}")
    ping_times["lost_connection_time"] = time.monotonic()


def ping_is_on_callback(ping_times):
    MolerTest.info("Ping works")
    if ping_times["lost_connection_time"] > 0:  # ping operable AFTER any net loss
        if ping_times["reconnection_time"] == 0:
            ping_times["reconnection_time"] = time.monotonic()
            outage_time = ping_times["reconnection_time"] - ping_times["lost_connection_time"]
            MolerTest.info(f"Network outage time is {outage_time}")


def test_network_outage():
    load_config(config=os.path.abspath('config/my_devices.yml'))
    unix1 = DeviceFactory.get_device(name='MyMachine1')
    unix2 = DeviceFactory.get_device(name='MyMachine2')

    # test setup
    ping_times = {"lost_connection_time": 0,
                  "reconnection_time": 0}
    # ensure network is up before running test
    net_up = unix2.get_cmd(cmd_name="ifconfig", cmd_params={"options": "lo up"})
    sudo_ensure_net_up = unix2.get_cmd(cmd_name="sudo", cmd_params={"password": "moler", "cmd_object": net_up})
    sudo_ensure_net_up()
    # run event observing "network down/up"
    no_ping = unix1.get_event(event_name="ping_no_response")
    no_ping.add_event_occurred_callback(callback=outage_callback,
                                        callback_params={'device_name': 'MyMachine1',
                                                         'ping_times': ping_times})
    no_ping.start()
    ping_is_on = unix1.get_event(event_name="ping_response")
    ping_is_on.add_event_occurred_callback(callback=ping_is_on_callback, 
                                           callback_params={'ping_times': ping_times})
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
*** calculating network outage time ***

1. run it
2. see logs - look for "Network outage" and "Ping works"
   - be carefull in logs analysis - what's wrong?
3. fix incorrect calculation by exchanging:
   no_ping = unix1.get_event(event_name="ping_no_response")
   into:
   no_ping = unix1.get_event(event_name="ping_no_response", event_params={"till_occurs_times": 1})
"""
