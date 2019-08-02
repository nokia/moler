import os.path
from moler.config import load_config
from moler.device.device import DeviceFactory


def test_network_outage():
    load_config(config=os.path.abspath('my_devices.yml'))
    unix1 = DeviceFactory.get_device(name='MyMachine1')
    unix2 = DeviceFactory.get_device(name='MyMachine2')


if __name__ == '__main__':
    test_network_outage()

"""
copy this file into workshop1/network_outage.py
1. run it
2. check logs
3. add PATH to LOGGER configuration & check logs
   - if not given then logs are created is current working directory
4. add RAW_LOG: True & check logs
5. add DEBUG_LEVEL: DEBUG & check logs
6. add DATE_FORMAT: "%Y-%m-%d %H:%M:%S" & check logs
"""
