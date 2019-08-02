import os.path
import time
from moler.config import load_config
from moler.device.device import DeviceFactory


def test_network_outage():


    #load_config(config=os.path.abspath('my_devices.yml'))


    load_config(config=os.path.abspath('config/my_devices.yml'))
    unix1 = DeviceFactory.get_device(name='MyMachine1')
    unix2 = DeviceFactory.get_device(name='MyMachine2')
    ping = unix1.get_cmd(cmd_name="ping", cmd_params={"destination": "localhost", "options": "-O"})
    #ping(timeout=10)
    ping.start(timeout=120)
    time.sleep(5)


if __name__ == '__main__':
    test_network_outage()

"""
copy this file into workshop1/network_outage.py
0. how do we know cmd_params for ping?
   - see moler/cmd/unix/ping.py in this repository or
   - see https://github.com/nokia/moler/blob/master/moler/cmd/unix/ping.py
   - constructor parameters
   - build_command_string()
   - COMMAND_OUTPUT & COMMAND_KWARGS
1. run it - command in foreground
2. start command into background
2. uncomment sleep to see that exiting python is killing still running commands (they stop themselves by Ctrl-C)
3. understand device log and raw log
4. see runner shutdown in moler.debug.log
"""

