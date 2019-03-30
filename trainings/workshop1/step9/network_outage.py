import os.path
import time
from moler.config import load_config
from moler.device.device import DeviceFactory


def outage_callback():
    print("Network outage")


def test_network_outage():
    load_config(config=os.path.abspath('config/my_devices.yml'))
    unix1 = DeviceFactory.get_device(name='MyMachine1')
    unix2 = DeviceFactory.get_device(name='MyMachine2')

    # test setup - ensure network is up before running test
    net_up = unix2.get_cmd(cmd_name="ifconfig", cmd_params={"options": "lo up"})
    sudo_ensure_net_up = unix2.get_cmd(cmd_name="sudo", cmd_params={"password": "moler", "cmd_object": net_up})
    sudo_ensure_net_up()
    # run event observing "network down"
    no_ping = unix1.get_event(event_name="ping_no_response")
    no_ping.add_event_occurred_callback(callback=outage_callback, callback_params={})
    no_ping.start()

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
*** react on event occurring in background ***

1. Answer: is shifting no_ping.start() after sudo_ifconfig_down() correct?
   No, even if it may work this creates danged of missing data.
   You should have up-and-running event observing connection's data
   before triggering action (ifconfig down) that may cause "observed data" to appear on connection
   
   So, generic hint: start all your events during test setup 
   
2. run it - see "Network outage" on console
3. see logs - look for "Network outage"

4. To have something in logs you need to exchange:
     print("Network outage")
   with:
     from moler.util.moler_test import MolerTest
     MolerTest.info("Network outage")
 
"""
